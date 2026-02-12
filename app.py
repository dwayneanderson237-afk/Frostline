import json
import os
import random
import sqlite3
import smtplib
from datetime import datetime
from functools import wraps
from email.message import EmailMessage

from flask import (
    Flask,
    render_template,
    abort,
    request,
    redirect,
    url_for,
    session,
    flash,
    Response,
    send_from_directory,
)
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")
app.config["ADMIN_USERNAME"] = os.environ.get("ADMIN_USERNAME", "admin")
app.config["ADMIN_PASSWORD"] = os.environ.get("ADMIN_PASSWORD", "admin123")
app.config["SMTP_HOST"] = os.environ.get("SMTP_HOST", "")
app.config["SMTP_PORT"] = int(os.environ.get("SMTP_PORT", "587"))
app.config["SMTP_USER"] = os.environ.get("SMTP_USER", "")
app.config["SMTP_PASS"] = os.environ.get("SMTP_PASS", "")
app.config["SMTP_USE_TLS"] = os.environ.get("SMTP_USE_TLS", "true").lower() == "true"
app.config["SMTP_USE_SSL"] = os.environ.get("SMTP_USE_SSL", "false").lower() == "true"
app.config["SMTP_FROM"] = os.environ.get("SMTP_FROM", "info@frostlinecoons.com")
app.config["SMTP_TO"] = os.environ.get("SMTP_TO", "info@frostlinecoons.com")
app.config["GA_MEASUREMENT_ID"] = os.environ.get("GA_MEASUREMENT_ID", "")
app.config["RESERVATION_DEPOSIT"] = float(os.environ.get("RESERVATION_DEPOSIT", "300"))
app.config["MAX_CONTENT_LENGTH"] = 80 * 1024 * 1024
app.config["UPLOADS_PATH"] = os.environ.get(
    "UPLOADS_PATH", os.path.join(app.root_path, "static", "uploads")
)
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 60 * 60 * 24 * 30

DATABASE = os.environ.get(
    "DATABASE_PATH", os.path.join(app.root_path, "frostline_coons.db")
)
ALLOWED_KITTEN_IMAGE_EXTS = {".jpg", ".jpeg"}
ALLOWED_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_VIDEO_EXTS = {".mp4", ".webm", ".mov"}

if app.config["UPLOADS_PATH"]:
    os.makedirs(app.config["UPLOADS_PATH"], exist_ok=True)

if DATABASE:
    db_dir = os.path.dirname(DATABASE)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

# -------------------- DEFAULT CONTENT --------------------
DEFAULT_SEO_KEYWORDS = [
    "Maine Coon kittens for sale",
    "Maine Coon kitten for sale",
    "Maine Coon kittens near me",
    "Maine Coon kitten near me",
    "Maine Coon cats for sale",
    "Maine Coon breeder",
    "Maine Coon breeder near me",
    "Maine Coon cattery",
    "Maine Coon cattery near me",
    "buy Maine Coon kitten",
    "reserve Maine Coon kitten",
    "Maine Coon kittens available",
    "Maine Coon kittens for adoption",
    "purebred Maine Coon kittens",
    "TICA registered Maine Coon kittens",
    "CFA registered Maine Coon kittens",
    "Maine Coon kittens delivery",
    "Maine Coon kitten delivery",
    "Maine Coon kitten shipping",
    "Maine Coon kitten transport",
    "Maine Coon kittens health guarantee",
    "Maine Coon breeder USA",
    "Maine Coon kittens USA",
    "Maine Coon kittens for sale USA",
]

STATE_SERVICE_AREAS = [
    "Ohio",
    "Texas",
    "Florida",
    "Tennessee",
    "Kentucky",
    "New York",
]

CITY_SERVICE_AREAS = [
    "Columbus",
    "Cleveland",
    "Cincinnati",
    "Austin",
    "Dallas",
    "Houston",
    "San Antonio",
    "Miami",
    "Orlando",
    "Tampa",
    "Nashville",
    "Memphis",
    "Louisville",
    "Lexington",
    "New York City",
    "Buffalo",
]

location_keywords = []
for state in STATE_SERVICE_AREAS:
    location_keywords.extend(
        [
            f"Maine Coon kittens for sale in {state}",
            f"Maine Coon breeder in {state}",
            f"Maine Coon kittens {state}",
        ]
    )

for city in CITY_SERVICE_AREAS:
    location_keywords.extend(
        [
            f"Maine Coon kittens for sale in {city}",
            f"Maine Coon breeder in {city}",
        ]
    )

DEFAULT_SEO_KEYWORDS.extend(location_keywords)

DEFAULT_SETTINGS = {
    "business_name": "Frostline Coons",
    "reply_to_email": "hello@frostlinecoons.com",
    "inquiry_email": "info@frostlinecoons.com",
    "business_address": "123 Frostline Lane, Columbus, OH 43215",
    "business_phone": "",
    "seo_keywords": ", ".join(dict.fromkeys(DEFAULT_SEO_KEYWORDS)),
    "service_areas": ", ".join(STATE_SERVICE_AREAS),
    "ga_measurement_id": "",
    "social_facebook": "https://facebook.com",
    "social_instagram": "https://instagram.com",
    "social_twitter": "https://twitter.com",
}
DEFAULT_KITTENS = [
    {
        "id": 1,
        "name": "Luna",
        "age": 4,
        "gender": "Female",
        "personality": "Playful, affectionate",
        "price": 1200,
        "folder": "kitten01",
        "image_count": 3,
        "featured": True,
        "health_details": "Vaccinated, dewormed, microchipped. Healthy and active.",
        "color": "Black and white tuxedo",
        "coat": "Silky medium coat",
        "energy": "Playful",
        "good_with": ["Kids", "Gentle dogs", "Other cats"],
        "bio": "Confident and curious, Luna loves window perches and following you from room to room.",
        "highlights": [
            "Loves feather toys and wand play",
            "Litter trained and uses scratch posts",
            "Soft trilling purr when picked up"
        ]
    },
    {
        "id": 2,
        "name": "Leo",
        "age": 5,
        "gender": "Male",
        "personality": "Curious, friendly",
        "price": 1300,
        "folder": "leo",
        "image_count": 3,
        "featured": True,
        "health_details": "All health checks done. Very social and playful.",
        "color": "Brown tabby with white",
        "coat": "Fluffy, classic Maine Coon coat",
        "energy": "High",
        "good_with": ["Kids", "Active homes", "Other cats"],
        "bio": "Leo is outgoing and bold, always the first to greet visitors and investigate new toys.",
        "highlights": [
            "Big playful personality",
            "Enjoys climbing and tall perches",
            "Gentle, sociable temperament"
        ]
    },
    {
        "id": 3,
        "name": "Milo",
        "age": 3,
        "gender": "Male",
        "personality": "Gentle, cuddly",
        "price": 1100,
        "folder": "milo",
        "image_count": 3,
        "featured": True,
        "health_details": "Healthy, fully vaccinated, loves attention.",
        "color": "Black smoke",
        "coat": "Soft plush coat",
        "energy": "Calm",
        "good_with": ["Quiet homes", "Adults", "Calm cats"],
        "bio": "Milo is a lap-seeker with a mellow vibe who bonds quickly and loves slow head rubs.",
        "highlights": [
            "Excellent lap companion",
            "Quiet and steady temperament",
            "Very gentle with handling"
        ]
    },
    {
        "id": 4,
        "name": "Nala",
        "age": 6,
        "gender": "Female",
        "personality": "Independent, smart",
        "price": 1250,
        "folder": "kitten02",
        "image_count": 3,
        "featured": True,
        "health_details": "Excellent health, dewormed, microchipped.",
        "color": "Warm red tabby",
        "coat": "Thick, water-resistant coat",
        "energy": "Medium",
        "good_with": ["Adults", "Calm dogs", "Other cats"],
        "bio": "Nala is bright and composed, happiest when she has a cozy perch to survey her world.",
        "highlights": [
            "Quick learner with toys and puzzles",
            "Polite and tidy manners",
            "Affectionate on her terms"
        ]
    },
    {
        "id": 5,
        "name": "Simba",
        "age": 4,
        "gender": "Male",
        "personality": "Loyal, curious",
        "price": 1350,
        "folder": "kitten03",
        "image_count": 3,
        "featured": True,
        "health_details": "Fully vaccinated and monitored daily.",
        "color": "Silver tabby",
        "coat": "Shaggy, lion-like ruff",
        "energy": "Medium-high",
        "good_with": ["Kids", "Dogs", "Other cats"],
        "bio": "Simba is confident and playful, with a big heart and a gentle, steady presence.",
        "highlights": [
            "Loves interactive play",
            "Great with new environments",
            "Follows you like a shadow"
        ]
    },
    {
        "id": 6,
        "name": "Chloe",
        "age": 5,
        "gender": "Female",
        "personality": "Playful, loving",
        "price": 1400,
        "folder": "kitten04",
        "image_count": 3,
        "featured": True,
        "health_details": "Vaccinated, healthy, loves to cuddle.",
        "color": "Blue (gray) with white",
        "coat": "Silky and dense",
        "energy": "Playful",
        "good_with": ["Kids", "Other cats", "First-time owners"],
        "bio": "Chloe is a social butterfly who melts into your arms and loves gentle grooming.",
        "highlights": [
            "Very affectionate and people-focused",
            "Enjoys brushing and belly rubs",
            "Sweet, soft purrs"
        ]
    },
    {
        "id": 7,
        "name": "Oliver",
        "age": 3,
        "gender": "Male",
        "personality": "Friendly",
        "price": 1100,
        "folder": "kitten05",
        "image_count": 3,
        "featured": False,
        "health_details": "Healthy and playful.",
        "color": "Brown tabby",
        "coat": "Medium-long, fluffy coat",
        "energy": "High",
        "good_with": ["Kids", "Active homes", "Other cats"],
        "bio": "Oliver is the explorer of the group, always curious and happy to meet new people.",
        "highlights": [
            "Excellent play drive",
            "Confident and outgoing",
            "Quick to learn routines"
        ]
    },
    {
        "id": 8,
        "name": "Daisy",
        "age": 4,
        "gender": "Female",
        "personality": "Sweet",
        "price": 1150,
        "folder": "Kitten08",
        "image_count": 3,
        "featured": False,
        "health_details": "Vaccinated and energetic.",
        "color": "Cream tabby",
        "coat": "Soft, plush coat",
        "energy": "Medium",
        "good_with": ["Kids", "Calm dogs", "Other cats"],
        "bio": "Daisy is gentle and affectionate, happiest curled beside you or near a sunny window.",
        "highlights": [
            "Soft, quiet temperament",
            "Enjoys gentle play",
            "Very cuddly in the evenings"
        ]
    },
    {
        "id": 9,
        "name": "Max",
        "age": 5,
        "gender": "Male",
        "personality": "Curious",
        "price": 1200,
        "folder": "kitten01",
        "image_count": 3,
        "featured": False,
        "health_details": "Healthy, loves exploring.",
        "color": "Black and white",
        "coat": "Dense, weather-ready coat",
        "energy": "Medium-high",
        "good_with": ["Kids", "Other cats", "Active homes"],
        "bio": "Max is bold and inquisitive, always checking out new rooms and toys.",
        "highlights": [
            "Great confidence and curiosity",
            "Plays well with others",
            "Loves climbing"
        ]
    },
    {
        "id": 10,
        "name": "Lily",
        "age": 3,
        "gender": "Female",
        "personality": "Cuddly",
        "price": 1100,
        "folder": "kitten02",
        "image_count": 3,
        "featured": False,
        "health_details": "Friendly and vaccinated.",
        "color": "Red tabby with white",
        "coat": "Feathery long coat",
        "energy": "Calm",
        "good_with": ["Adults", "Quiet homes", "Other cats"],
        "bio": "Lily is serene and affectionate, preferring cozy spaces and gentle attention.",
        "highlights": [
            "A calm, soothing presence",
            "Loves lap time",
            "Very gentle with handling"
        ]
    },
    {
        "id": 11,
        "name": "Charlie",
        "age": 4,
        "gender": "Male",
        "personality": "Gentle",
        "price": 1250,
        "folder": "kitten03",
        "image_count": 3,
        "featured": False,
        "health_details": "Healthy, playful, loves humans.",
        "color": "Silver tabby",
        "coat": "Thick, plush coat",
        "energy": "Medium",
        "good_with": ["Kids", "Other cats", "First-time owners"],
        "bio": "Charlie is easygoing and affectionate, with a soft purr and a sweet nature.",
        "highlights": [
            "Balanced energy",
            "Affectionate and steady",
            "Great family companion"
        ]
    },
    {
        "id": 12,
        "name": "Bella",
        "age": 5,
        "gender": "Female",
        "personality": "Smart",
        "price": 1300,
        "folder": "kitten04",
        "image_count": 3,
        "featured": False,
        "health_details": "Vaccinated, curious, friendly.",
        "color": "Blue tortie",
        "coat": "Velvety, thick coat",
        "energy": "Medium-high",
        "good_with": ["Adults", "Kids", "Other cats"],
        "bio": "Bella is clever and curious, always interested in puzzle toys and new routines.",
        "highlights": [
            "Quick learner",
            "Playful and attentive",
            "Enjoys interactive toys"
        ]
    },
    {
        "id": 13,
        "name": "Oscar",
        "age": 3,
        "gender": "Male",
        "personality": "Playful",
        "price": 1100,
        "folder": "kitten05",
        "image_count": 3,
        "featured": False,
        "health_details": "Active and healthy.",
        "color": "Classic brown tabby",
        "coat": "Long, fluffy coat",
        "energy": "High",
        "good_with": ["Kids", "Active homes", "Other cats"],
        "bio": "Oscar is energetic and silly, always ready to chase a toy or hop onto a perch.",
        "highlights": [
            "Very playful and athletic",
            "Social and outgoing",
            "Loves wand toys"
        ]
    },
    {
        "id": 14,
        "name": "Mia",
        "age": 4,
        "gender": "Female",
        "personality": "Affectionate",
        "price": 1150,
        "folder": "kitten01",
        "image_count": 3,
        "featured": False,
        "health_details": "Vaccinated and loving.",
        "color": "Black and white",
        "coat": "Soft, silky coat",
        "energy": "Medium",
        "good_with": ["Kids", "Other cats", "Calm dogs"],
        "bio": "Mia is affectionate and steady, happy to curl up beside you at the end of the day.",
        "highlights": [
            "Very people-focused",
            "Gentle and patient",
            "Sweet, steady temperament"
        ]
    },
    {
        "id": 15,
        "name": "Jack",
        "age": 5,
        "gender": "Male",
        "personality": "Loyal",
        "price": 1200,
        "folder": "kitten02",
        "image_count": 3,
        "featured": False,
        "health_details": "Healthy and playful.",
        "color": "Red tabby",
        "coat": "Thick and fluffy",
        "energy": "Medium",
        "good_with": ["Kids", "Adults", "Other cats"],
        "bio": "Jack is calm and loyal, with a gentle presence and an affectionate personality.",
        "highlights": [
            "Easygoing and steady",
            "Great with families",
            "Enjoys relaxed play"
        ]
    },
    {
        "id": 16,
        "name": "Lucy",
        "age": 3,
        "gender": "Female",
        "personality": "Sweet",
        "price": 1100,
        "folder": "kitten03",
        "image_count": 3,
        "featured": False,
        "health_details": "Friendly and healthy.",
        "color": "Silver tabby with white",
        "coat": "Feathery long coat",
        "energy": "Calm",
        "good_with": ["Quiet homes", "Adults", "Other cats"],
        "bio": "Lucy is gentle and sweet, preferring calm spaces and soft, reassuring attention.",
        "highlights": [
            "Very calm temperament",
            "Loves quiet cuddles",
            "Great for relaxed homes"
        ]
    }
]

DEFAULT_TESTIMONIALS = [
    {
        "author": "Ava Martinez",
        "quote": "Our kitten arrived confident and social. The care and communication were incredible.",
        "image": "images/doherty.jpg"
    },
    {
        "author": "Jordan Wells",
        "quote": "Sweet temperament and beautiful coat. We felt supported from day one.",
        "image": "images/fluffy.jpg"
    },
    {
        "author": "Priya Mehta",
        "quote": "Healthy, playful, and already attached to our family. Best decision we made.",
        "image": "images/jack.jpg"
    },
    {
        "author": "Ethan Nguyen",
        "quote": "The most gentle kitten. Calm with kids and so easy to handle.",
        "image": "images/misty.jpg"
    },
    {
        "author": "Ella Carter",
        "quote": "The temperament matching was spot on. Our kitten fits us perfectly.",
        "image": "images/nono.jpg"
    },
    {
        "author": "Marcus Patel",
        "quote": "Clear health records and a smooth process. We felt confident the whole time.",
        "image": "images/kanashi-7NcdSLcRTq8-unsplash.jpg"
    },
    {
        "author": "Zoe Rivera",
        "quote": "Playful, affectionate, and incredibly smart. Our home feels complete now.",
        "image": "images/bee-felten-leidel-DkYlK2vyuZg-unsplash.jpg"
    },
    {
        "author": "Samira Khan",
        "quote": "The kitten settled in within days. Loving, curious, and full of personality.",
        "image": "images/bobbi-wu-UN6uVzke__g-unsplash.jpg"
    }
]

DEFAULT_SECTIONS = [
    {
        "key": "logo",
        "title": "Frostline Coons",
        "body": "",
        "image": ""
    },
    {
        "key": "hero",
        "title": "Frostline Coons",
        "body": (
            "A cattery built on patience, ethics, and devotion. "
            "We don’t rush kittens into the world — we raise companions for life."
        ),
        "image": "images/hero_kitten.jpg"
    },
    {
        "key": "hero_slide_2",
        "title": "Raised for Real Homes",
        "body": "Daily handling, gentle routines, and confident temperaments built from the very start.",
        "image": "images/hero_home.jpg"
    },
    {
        "key": "hero_slide_3",
        "title": "Safe Travel, Calm Arrivals",
        "body": "Thoughtful travel planning by ground or air, with comfort and communication throughout.",
        "image": "images/hero_delivery.jpg"
    },
    {
        "key": "story",
        "title": "Our Story",
        "body": (
            "Frostline Coons was never meant to be fast, loud, or commercial. "
            "It began quietly — with research, lineage study, late nights, "
            "and a refusal to cut corners. Every kitten carries intention. "
            "We raise in small, carefully planned litters so each kitten "
            "gets hands-on socialization from day one.\n\n"
            "Our foundation is built on transparency and care: we document "
            "every stage of growth, prioritize clean spaces, and focus on "
            "temperaments that thrive in real homes. We want families to "
            "meet a kitten whose personality already feels like a perfect fit."
        ),
        "image": "images/story.jpg"
    },
    {
        "key": "health",
        "title": "Health & Care",
        "body": (
            "Genetics tested. Vet monitored. Nutrition curated. "
            "We raise slowly so bodies grow strong and minds stay gentle. "
            "Each kitten receives a full wellness plan, early social training, "
            "and careful introductions to grooming and handling.\n\n"
            "We use premium, balanced nutrition and keep detailed records "
            "of milestones, vaccines, and behavioral development so you "
            "can feel confident from the first day home."
        ),
        "image": "images/health.jpg"
    },
    {
        "key": "mission",
        "title": "Our Mission",
        "body": (
            "To preserve the Maine Coon with honesty. "
            "To protect families from unethical breeding. "
            "To stand behind every kitten — for life. "
            "We place only when the match is right, with long-term support "
            "and guidance included.\n\n"
            "This is a lifelong promise to families and to the breed we love: "
            "thoughtful practices, ethical standards, and cats that are healthy, "
            "confident, and deeply social."
        ),
        "image": "images/mission.jpg"
    },
    {
        "key": "travel",
        "title": "How I Travel to You",
        "body": (
            "Flight Nanny | Hand-delivered in cabin with a dedicated caregiver.\n"
            "Air Cargo | Climate-controlled travel with direct flights when possible.\n"
            "Ground Nanny | Personal ground transport with comfort breaks built in.\n"
            "Owner Pickup | Meet at our cattery or a nearby airport for handoff."
        ),
        "image": ""
    },
    {
        "key": "health_check",
        "title": "Health Check & Guarantees",
        "body": (
            "Veterinary health exam\n"
            "Age-appropriate vaccinations\n"
            "Deworming schedule completed\n"
            "FIV/FeLV screening\n"
            "Health certificate (when required)\n"
            "Wellness records provided\n"
            "Early socialization and handling\n"
            "Nutrition plan and transition guide"
        ),
        "image": ""
    },
    {
        "key": "adoption_journey",
        "title": "Your Adoption Journey",
        "body": (
            "Choose & Reserve | Select your kitten and place a reservation.\n"
            "Prepare & Plan | We confirm timing, care checklist, and travel plan.\n"
            "Safe Delivery | Your kitten travels with updates and comfort care.\n"
            "Homecoming Support | We guide you through the first days at home."
        ),
        "image": ""
    }
]

DEFAULT_PAGES = [
    {
        "slug": "delivery",
        "title": "Delivery & Arrival",
        "meta_title": "Maine Coon Kitten Delivery | Frostline Coons",
        "meta_description": "Learn how our Maine Coon kittens travel safely by ground or air, from pickup to arrival at your home or airport.",
        "hero_title": "Delivery & Arrival",
        "hero_body": (
            "From pickup to your front door (or airport handoff), our process is structured, calm, and kitten-first. "
            "We offer safe ground transport and carefully coordinated air travel with clear communication at every step."
        ),
        "hero_image": "images/hero_delivery.jpg",
        "steps": [
            {
                "title": "Preparation",
                "body": "We confirm paperwork, vet records, and travel requirements. Each kitten travels with familiar bedding, hydration, and a calm routine."
            },
            {
                "title": "Safe Transport",
                "body": "Choose ground or air options. Both routes are climate controlled, monitored, and planned for gentle handling and rest breaks."
            },
            {
                "title": "Arrival Support",
                "body": "We guide you through the first 48 hours at home, including feeding, settling tips, and introductions to your space."
            }
        ],
        "blocks": [
            {
                "title": "Pickup & Preparation",
                "body": "Each journey begins with a calm pickup routine. Kittens receive a final wellness check, hydration, and a familiar scent item to reduce stress.",
                "image": "images/care.jpg",
                "layout": "left"
            },
            {
                "title": "Ground Transport",
                "body": "Ground transport is ideal for regional deliveries. Our carriers are temperature controlled and routed for minimal time on the road.",
                "image": "images/health2.jpg",
                "layout": "right"
            },
            {
                "title": "Air Transport & Airport Pickup",
                "body": "For longer distances, we coordinate air travel with trusted couriers and pet-safe airline policies with a smooth airport handoff.",
                "image": "images/her.jpg",
                "layout": "left"
            },
            {
                "title": "Arrival at Home",
                "body": "We recommend a quiet room for the first day with water, food, and a soft bed. Let your kitten explore slowly and set their pace.",
                "image": "images/hero_home.jpg",
                "layout": "right"
            }
        ],
        "cta_title": "Questions About Delivery?",
        "cta_body": "We’ll help you choose the best option for your location and timeline. Reach out and we’ll guide you from reservation to arrival.",
        "cta_label": "Contact Us",
        "cta_link": "mailto:info@frostlinecoons.com"
    },
    {
        "slug": "about",
        "title": "About Frostline Coons",
        "meta_title": "About Frostline Coons | Maine Coon Breeder",
        "meta_description": "Learn about Frostline Coons, our breeding philosophy, and the care we provide for every Maine Coon kitten.",
        "hero_title": "About Frostline Coons",
        "hero_body": (
            "We raise Maine Coons with patience, transparency, and deep respect for the breed. "
            "Every kitten is socialized, nurtured, and matched carefully to the right home."
        ),
        "hero_image": "images/story.jpg",
        "steps": [],
        "blocks": [
            {
                "title": "Our Philosophy",
                "body": (
                    "We focus on small, carefully planned litters so each kitten receives daily handling and enrichment. "
                    "Health testing, clear communication, and ethical practices guide every decision."
                ),
                "image": "images/mission.jpg",
                "layout": "left"
            },
            {
                "title": "Early Socialization",
                "body": (
                    "Kittens are introduced to grooming, gentle handling, and everyday household sounds early. "
                    "This helps them grow into calm, confident companions."
                ),
                "image": "images/health.jpg",
                "layout": "right"
            },
            {
                "title": "Lifelong Support",
                "body": (
                    "We stay connected with families after pickup or delivery. "
                    "From feeding tips to temperament guidance, we’re here for you."
                ),
                "image": "images/hero_home.jpg",
                "layout": "left"
            }
        ],
        "cta_title": "Want to Learn More?",
        "cta_body": "We’re happy to answer questions about temperament, care, and availability.",
        "cta_label": "Email Us",
        "cta_link": "mailto:info@frostlinecoons.com"
    },
    {
        "slug": "faqs",
        "title": "Frequently Asked Questions",
        "meta_title": "Maine Coon FAQs | Frostline Coons",
        "meta_description": "Answers to common questions about Maine Coon kittens, care routines, and our adoption process.",
        "hero_title": "Frequently Asked Questions",
        "hero_body": (
            "Everything you need to know about our process, kitten care, and delivery options."
        ),
        "hero_image": "images/health2.jpg",
        "steps": [],
        "blocks": [
            {
                "title": "When do kittens go home?",
                "body": (
                    "Kittens typically go home after they are fully weaned, socialized, and cleared by the vet. "
                    "We prioritize health and confidence over speed."
                ),
                "image": "images/care.jpg",
                "layout": "left"
            },
            {
                "title": "Do you offer delivery?",
                "body": (
                    "Yes. We provide ground transport and air travel options depending on location and timing. "
                    "All deliveries are planned with the kitten’s comfort in mind."
                ),
                "image": "images/hero_delivery.jpg",
                "layout": "right"
            },
            {
                "title": "How do I prepare my home?",
                "body": (
                    "Set up a quiet starter room with food, water, litter, and a cozy bed. "
                    "We provide a transition guide with each kitten."
                ),
                "image": "images/hero_home.jpg",
                "layout": "left"
            }
        ],
        "cta_title": "Still Have Questions?",
        "cta_body": "Reach out and we’ll guide you through the next steps.",
        "cta_label": "Contact Us",
        "cta_link": "mailto:info@frostlinecoons.com"
    },
    {
        "slug": "contact",
        "title": "Contact Frostline Coons",
        "meta_title": "Contact Frostline Coons | Maine Coon Kittens",
        "meta_description": "Get in touch with Frostline Coons for availability, delivery questions, and kitten care guidance.",
        "hero_title": "Contact Frostline Coons",
        "hero_body": (
            "We respond quickly and personally. Tell us about your home, your timeline, and the kitten you’re looking for."
        ),
        "hero_image": "images/hero_kitten.jpg",
        "steps": [],
        "blocks": [
            {
                "title": "Email",
                "body": "info@frostlinecoons.com — We respond within 24–48 hours.",
                "image": "images/about1.jpg",
                "layout": "left"
            },
            {
                "title": "Delivery Questions",
                "body": "Let us know your location and preferred timing. We’ll recommend the safest transport option.",
                "image": "images/hero_delivery.jpg",
                "layout": "right"
            }
        ],
        "cta_title": "Ready to Start?",
        "cta_body": "Send a message and we’ll help you find the right kitten.",
        "cta_label": "Email Us",
        "cta_link": "mailto:info@frostlinecoons.com"
    }
]

DEFAULT_BLOG_POSTS = [
    {
        "title": "Maine Coon Temperament: What to Expect at Home",
        "excerpt": "A buyer-focused look at Maine Coon temperament, daily routines, and how to match the right personality to your home.",
        "content": (
            "Maine Coons are often called gentle giants, but their temperament is more nuanced than a single phrase. "
            "They are typically social, curious, and steady, with a style that fits families who want a bonded companion "
            "without constant clinginess. Knowing what to expect helps you choose the right kitten and build a calm start.\n\n"
            "## Social but not demanding\n\n"
            "Most Maine Coons prefer to be near their people rather than on top of them. "
            "You will often see a kitten follow you from room to room, settle nearby, and check in with soft trills. "
            "This is a breed that enjoys companionship, but it also respects quiet time.\n\n"
            "A confident kitten will explore new spaces, then return to you for reassurance. "
            "That pattern is a strong sign of a balanced temperament: curious, friendly, and secure.\n\n"
            "## Play style and energy balance\n\n"
            "Maine Coons are playful without being frantic. They enjoy interactive play, puzzle feeders, and climbing, "
            "but they are usually content to relax afterward. Two to three short play sessions per day is ideal. "
            "If your household is active, a slightly higher energy kitten can be a great match.\n\n"
            "### Signs of a confident, stable temperament\n\n"
            "Look for kittens that approach new people with relaxed curiosity, recover quickly after a startle, "
            "and can settle calmly after play. These behaviors often predict an easy transition to a new home.\n\n"
            "## Communication and body language\n\n"
            "Maine Coons are known for chirps, trills, and soft conversational sounds. "
            "They also communicate with body language: a gently raised tail signals confidence, "
            "slow blinks show comfort, and a relaxed posture indicates trust. "
            "Learning these cues helps you respond calmly and build a stronger bond.\n\n"
            "## How temperament is shaped\n\n"
            "Genetics play a role, but early handling and routine matter just as much. "
            "Kittens who are gently handled, exposed to normal household sounds, and given predictable routines "
            "tend to become calmer adults. Ask your breeder how the litter is socialized and what the daily routine looks like.\n\n"
            "## Temperament with kids and other pets\n\n"
            "Maine Coons usually do well with respectful children and gentle pets. "
            "Slow introductions and a safe retreat space make a big difference. "
            "Teach kids to use soft voices and gentle hands, and keep early interactions short and positive.\n\n"
            "## Questions to ask before you reserve\n\n"
            "To match temperament, ask about each kitten's energy level, response to handling, and play preferences. "
            "Ask whether the kitten seeks attention or prefers independent play. "
            "These small details help you choose a kitten that fits your home.\n\n"
            "## The first week at home\n\n"
            "Temperament shines during the first week. A quiet starter room, consistent meals, and short play sessions "
            "help your kitten feel secure. Avoid overwhelming the kitten with visitors or large spaces immediately. "
            "When the routine is calm, Maine Coons typically settle quickly and show their affectionate side.\n\n"
            "A Maine Coon's temperament is a blend of gentle confidence and social curiosity. "
            "When you match that temperament to your lifestyle, the result is a steady, loyal companion for years to come."
        ),
        "meta_title": "Maine Coon Temperament Guide | Frostline Coons",
        "meta_description": "Learn what Maine Coon temperament is really like and how to choose the right personality match for your home.",
        "keywords": "Maine Coon temperament, Maine Coon personality, gentle giant cat",
        "cover_image": "https://source.unsplash.com/1600x900/?maine%20coon,cat&sig=101"
    },
    {
        "title": "How Big Do Maine Coons Get? Growth Stages Explained",
        "excerpt": "A detailed growth guide for Maine Coons, from early kitten months to full adult size.",
        "content": (
            "Maine Coons are famous for their size, but they also grow at a slower pace than most breeds. "
            "Understanding the growth timeline helps you plan nutrition, space, and expectations without rushing development.\n\n"
            "## The long growth timeline\n\n"
            "Most Maine Coons continue growing for three to five years. "
            "The first year brings the most visible change in height and length, while years two and three focus on filling out "
            "with muscle and a fuller coat. This slow growth is normal and healthy for the breed.\n\n"
            "## Growth stages at a glance\n\n"
            "### 0 to 4 months\n\n"
            "Rapid growth, high energy, and frequent meals. This stage builds the foundation for bones and joints. "
            "Expect a curious, energetic kitten who wants to climb and explore.\n\n"
            "### 4 to 9 months\n\n"
            "This is the lanky stage. Kittens often look tall and lean before their chest and frame fill out. "
            "Consistent nutrition and steady play help them build healthy muscle.\n\n"
            "### 9 to 18 months\n\n"
            "The body starts to fill out, and the coat becomes thicker. "
            "You may notice more width across the chest and shoulders.\n\n"
            "### 18 months to 3 years\n\n"
            "This stage is about slow, steady maturity. The cat continues to gain muscle and develop the classic Maine Coon build.\n\n"
            "## Size ranges and variation\n\n"
            "Adult size varies by genetics, gender, and activity. Males are often larger, but there is a wide range. "
            "Healthy size is more important than a specific number. "
            "Focus on steady, balanced growth rather than chasing a scale target.\n\n"
            "## Nutrition that supports healthy growth\n\n"
            "Large-breed kittens benefit from high-quality protein and balanced minerals. "
            "Avoid rapid weight gain from overfeeding, which can stress joints. "
            "A consistent feeding schedule with measured portions helps maintain steady growth.\n\n"
            "## Activity and joint support\n\n"
            "Maine Coons are athletic and enjoy climbing. "
            "Provide sturdy cat trees and interactive play, but avoid excessive high-impact jumping for very young kittens. "
            "Short, frequent play sessions are better than a single long session.\n\n"
            "## Monitoring growth at home\n\n"
            "Use a pet scale or a bathroom scale with a carrier to track weight monthly. "
            "Watch overall body condition: you should feel a slight rib outline without excess padding. "
            "If growth seems too fast or too slow, consult your vet for guidance.\n\n"
            "## When to ask your vet\n\n"
            "If your kitten loses weight, shows low appetite, or seems unusually lethargic, check in with your vet. "
            "Early evaluation prevents small issues from becoming bigger problems.\n\n"
            "Maine Coons grow into their size with time. "
            "A patient, steady approach to nutrition and activity produces the healthiest, most confident adult."
        ),
        "meta_title": "Maine Coon Size & Growth | Frostline Coons",
        "meta_description": "Learn the Maine Coon growth timeline, size ranges, and how to support healthy development.",
        "keywords": "Maine Coon size, Maine Coon growth, how big do Maine Coons get",
        "cover_image": "https://images.pexels.com/photos/236366/pexels-photo-236366.jpeg?cs=srgb&dl=pexels-pixabay-236366.jpg&fm=jpg"
    },
    {
        "title": "Maine Coon Grooming Routine: Brushes, Baths, and Mats",
        "excerpt": "A complete grooming routine for Maine Coons, including tools, schedules, and mat prevention.",
        "content": (
            "Maine Coons have a long, luxurious coat designed for cold climates, which means grooming is part of the routine. "
            "The goal is not perfection, but comfort: prevent mats, reduce shedding, and keep your kitten relaxed during handling.\n\n"
            "## The essential grooming tools\n\n"
            "### Wide-tooth comb\n\n"
            "A comb reaches the undercoat and helps prevent tangles near the skin. "
            "Use it first to separate fur before brushing.\n\n"
            "### Slicker brush\n\n"
            "A slicker brush smooths the topcoat and removes loose hair. "
            "Use gentle, short strokes to avoid pulling.\n\n"
            "### Dematting tool (optional)\n\n"
            "For stubborn mats, a dematting tool can help, but use it carefully and sparingly. "
            "If a mat is close to the skin, seek a professional groomer.\n\n"
            "## A weekly grooming schedule\n\n"
            "For most Maine Coons, two to three grooming sessions per week are enough. "
            "During seasonal sheds, increase frequency to keep the coat comfortable. "
            "Short sessions of five to ten minutes are easier for kittens than one long session.\n\n"
            "## Focus areas for mat prevention\n\n"
            "Friction areas are the most common mat locations: the chest ruff, belly, armpits, and behind the legs. "
            "These spots need extra attention, especially during spring and fall sheds.\n\n"
            "## Bathing: when and how\n\n"
            "Most Maine Coons do not need frequent baths. "
            "A bath is helpful after a messy adventure or during heavy seasonal shedding. "
            "Use warm water, a gentle cat shampoo, and a calm, slow approach. "
            "Dry thoroughly with a towel and a low-heat dryer if your kitten tolerates it.\n\n"
            "## Nail trims and basic hygiene\n\n"
            "Trim nails every two to four weeks, and handle paws gently during grooming to build trust. "
            "Check ears for debris and wipe with a soft, damp cotton pad if needed.\n\n"
            "## Training your kitten to enjoy grooming\n\n"
            "Start with very short sessions and reward calm behavior with treats. "
            "Let your kitten sniff the tools before you begin. "
            "Consistency matters more than speed; slow and steady builds a positive routine.\n\n"
            "## Common mistakes to avoid\n\n"
            "Avoid brushing too aggressively or forcing long sessions. "
            "Mats are easier to prevent than to remove, so regular light grooming is better than occasional heavy grooming.\n\n"
            "A simple, consistent routine keeps the Maine Coon coat healthy and beautiful. "
            "Grooming also becomes a bonding ritual that helps your kitten feel secure."
        ),
        "meta_title": "Maine Coon Grooming Tips | Frostline Coons",
        "meta_description": "A full Maine Coon grooming routine with tools, schedules, and mat prevention tips.",
        "keywords": "Maine Coon grooming, Maine Coon brush, long-haired cat grooming",
        "cover_image": "https://images.pexels.com/photos/460785/pexels-photo-460785.jpeg?cs=srgb&dl=pexels-pixabay-460785.jpg&fm=jpg"
    },
    {
        "title": "Kitten‑Proofing Your Home for a Maine Coon",
        "excerpt": "A room-by-room kitten-proofing plan designed for large, curious Maine Coon kittens.",
        "content": (
            "Maine Coon kittens are bold, athletic, and curious. "
            "A safe home setup protects your kitten and reduces stress during the first weeks. "
            "This room-by-room guide focuses on real-life hazards and smart fixes.\n\n"
            "## Start with a quiet starter room\n\n"
            "Choose a small room with a litter box, food, water, and a cozy bed. "
            "This gives your kitten a calm place to settle before exploring the full home. "
            "Keep the door closed at first to avoid overwhelm.\n\n"
            "## Living room safety\n\n"
            "Secure loose cords and power strips, and block access behind entertainment centers. "
            "Remove small swallowable items like rubber bands or hair ties. "
            "Stabilize tall furniture that could wobble if climbed.\n\n"
            "## Kitchen precautions\n\n"
            "Keep countertops clear of food scraps and sharp objects. "
            "Use child-safe latches on lower cabinets if you store cleaners or plastic bags. "
            "Ensure trash cans have secure lids.\n\n"
            "## Bathroom and laundry areas\n\n"
            "Always close toilet lids and keep cleaning products out of reach. "
            "Check laundry machines before use, as kittens love warm hiding spaces. "
            "Secure loose strings from towels or bath mats.\n\n"
            "## Bedrooms and closets\n\n"
            "Store strings, cords, and small accessories in drawers. "
            "Make sure window screens are secure and keep windows closed or limited. "
            "Offer a soft resting spot to discourage climbing on shelves.\n\n"
            "## Stairs, balconies, and outdoor access\n\n"
            "Use gates if needed for very young kittens, and avoid any unprotected balcony access. "
            "Maine Coons are excellent climbers, so safety barriers are essential.\n\n"
            "## Safe enrichment instead of risky exploration\n\n"
            "Provide a sturdy cat tree, scratching posts, and interactive toys. "
            "When kittens have safe outlets for climbing and play, they are less likely to explore hazards.\n\n"
            "## The first week checklist\n\n"
            "Keep the environment quiet, limit visitors, and let your kitten explore gradually. "
            "A slow, calm start builds confidence and reduces unwanted behaviors.\n\n"
            "Kitten-proofing is not about making your home perfect. "
            "It is about removing the biggest risks and giving your Maine Coon a safe, confident start."
        ),
        "meta_title": "Kitten Proofing for Maine Coons | Frostline Coons",
        "meta_description": "Room-by-room kitten-proofing tips to create a safe home for Maine Coon kittens.",
        "keywords": "kitten proofing, Maine Coon kitten home, cat safety tips",
        "cover_image": "https://source.unsplash.com/1600x900/?cat%20home&sig=102"
    },
    {
        "title": "Feeding a Maine Coon Kitten: Schedule and Nutrition Tips",
        "excerpt": "A practical feeding plan for Maine Coon kittens, with schedules, nutrition goals, and portion guidance.",
        "content": (
            "Feeding a Maine Coon kitten is about steady growth, strong joints, and long-term health. "
            "This breed grows slowly, so consistent nutrition matters more than rapid weight gain.\n\n"
            "## Nutrition priorities\n\n"
            "Look for high-quality protein, balanced fats, and the right mineral ratio for growing bones. "
            "Kitten-specific formulas are designed for development and are the safest base diet.\n\n"
            "## Feeding schedule by age\n\n"
            "### 8 to 12 weeks\n\n"
            "Offer four small meals per day. "
            "This keeps energy stable and supports digestion.\n\n"
            "### 3 to 6 months\n\n"
            "Move to three meals per day. "
            "Keep portions consistent and monitor energy levels.\n\n"
            "### 6 to 12 months\n\n"
            "Most kittens do well with two to three meals per day. "
            "Adjust portions based on body condition rather than weight alone.\n\n"
            "## Wet food, dry food, or both\n\n"
            "A combination can work well. Wet food supports hydration and can be easier to digest, "
            "while dry food offers convenience and helps with routine. "
            "Choose high-quality options either way.\n\n"
            "## Hydration matters\n\n"
            "Fresh water should be available at all times. "
            "Water fountains can encourage drinking and support coat health.\n\n"
            "## Treats and extras\n\n"
            "Keep treats minimal and use them for training or grooming rewards. "
            "Avoid dairy and high-salt human foods. "
            "If you want supplements, ask your vet first.\n\n"
            "## Transitioning foods safely\n\n"
            "If you change foods, do it over 7 to 10 days by slowly increasing the new food ratio. "
            "Monitor digestion and reduce speed if stools change.\n\n"
            "## Monitoring healthy growth\n\n"
            "Check body condition regularly. You should feel a light rib outline but not see sharp bones. "
            "Steady growth is the goal, not rapid size.\n\n"
            "A consistent, balanced feeding plan sets the foundation for a healthy adult Maine Coon. "
            "If you are unsure about portions, your vet can help you fine-tune the schedule."
        ),
        "meta_title": "Maine Coon Kitten Feeding Guide | Frostline Coons",
        "meta_description": "Maine Coon kitten feeding guide with schedules, nutrition goals, and hydration tips.",
        "keywords": "Maine Coon kitten food, feeding schedule, Maine Coon nutrition",
        "cover_image": "https://images.pexels.com/photos/96900/pexels-photo-96900.jpeg?cs=srgb&dl=pexels-dan-wheeler-96900.jpg&fm=jpg"
    },
    {
        "title": "Maine Coon vs. Other Breeds: Is the Gentle Giant Right for You?",
        "excerpt": "Compare Maine Coons with other popular breeds to see if their temperament and needs fit your home.",
        "content": (
            "Maine Coons are known for their relaxed, friendly nature and large size. They often enjoy social homes "
            "and do best with space to climb and explore.\n\n"
            "Compared to more independent breeds, Maine Coons are more likely to greet guests and follow family members "
            "throughout the day.\n\n"
            "If you want a calm, affectionate, and interactive cat, the Maine Coon is an excellent choice."
        ),
        "meta_title": "Maine Coon vs Other Cats | Frostline Coons",
        "meta_description": "See how Maine Coons compare to other cat breeds and decide if the gentle giant is right for your home.",
        "keywords": "Maine Coon vs, gentle giant cat, best family cat",
        "cover_image": "images/mission.jpg"
    },
    {
        "title": "Introducing a Maine Coon to Dogs",
        "excerpt": "A calm, step‑by‑step approach to building trust between your kitten and dog.",
        "content": (
            "Start with scent swapping before any face‑to‑face introductions. Let your Maine Coon explore in a safe room "
            "while your dog gets used to the new scent.\n\n"
            "Use leashes and baby gates for gradual visual introductions. Keep sessions short and positive.\n\n"
            "With patience and consistent routines, many Maine Coons bond well with gentle dogs."
        ),
        "meta_title": "Maine Coon and Dog Introductions | Frostline Coons",
        "meta_description": "Learn how to safely introduce a Maine Coon kitten to a dog using calm, positive steps.",
        "keywords": "Maine Coon with dogs, introducing cats to dogs, kitten dog introduction",
        "cover_image": "images/her.jpg"
    },
    {
        "title": "Litter Training Tips for Maine Coon Kittens",
        "excerpt": "Make litter training simple with the right box size, litter type, and routine.",
        "content": (
            "Maine Coon kittens do best with large, low‑entry litter boxes that match their size. "
            "Place boxes in quiet, easy‑to‑reach areas.\n\n"
            "Stick to unscented, fine‑grained litter at first and keep the box exceptionally clean. "
            "Consistency is the key to reliable habits.\n\n"
            "If accidents happen, stay calm and gently redirect — most kittens learn quickly with routine."
        ),
        "meta_title": "Maine Coon Litter Training | Frostline Coons",
        "meta_description": "Easy litter training tips for Maine Coon kittens, including box size, litter type, and routines.",
        "keywords": "Maine Coon litter training, kitten litter tips, cat litter box size",
        "cover_image": "images/care.jpg"
    },
    {
        "title": "Understanding Maine Coon Coat Colors and Patterns",
        "excerpt": "From tabby to smoke, learn how Maine Coon colors are described and what to expect as they grow.",
        "content": (
            "Maine Coon colors range from classic tabby patterns to solid, smoke, and bi‑color coats. "
            "Kittens often change tone as their coat develops.\n\n"
            "Pattern names describe distribution: mackerel, classic, spotted, or ticked. "
            "A kitten’s adult coat typically appears after the first major shed.\n\n"
            "Color is purely cosmetic, but it’s fun to follow how their look evolves over time."
        ),
        "meta_title": "Maine Coon Colors & Patterns | Frostline Coons",
        "meta_description": "Learn the most common Maine Coon coat colors and patterns, and how they develop as kittens grow.",
        "keywords": "Maine Coon colors, Maine Coon patterns, tabby Maine Coon",
        "cover_image": "images/doherty.jpg"
    },
    {
        "title": "Maine Coon Health: Screening, Vet Visits, and Common Questions",
        "excerpt": "A practical overview of wellness checks, genetic screening, and routine care for Maine Coons.",
        "content": (
            "Responsible breeders prioritize genetic screening and early wellness checks. "
            "Routine vet visits help detect issues early and keep kittens on track.\n\n"
            "Ask about health records, vaccination schedules, and parasite prevention. "
            "These basics protect your kitten during the most sensitive stages.\n\n"
            "Consistent care creates a foundation for a long, healthy life."
        ),
        "meta_title": "Maine Coon Health & Vet Care | Frostline Coons",
        "meta_description": "Learn about health screening, vet schedules, and common questions for Maine Coon kitten care.",
        "keywords": "Maine Coon health, cat vet schedule, kitten wellness",
        "cover_image": "images/health.jpg"
    },
    {
        "title": "How to Travel Safely with a Maine Coon",
        "excerpt": "Whether it’s a vet visit or a longer trip, here’s how to keep travel calm and stress‑free.",
        "content": (
            "Start by making the carrier a positive space with familiar bedding and treats. "
            "Short practice rides can reduce travel anxiety.\n\n"
            "During travel, keep the carrier level and secure. "
            "Avoid loud music and sudden temperature changes.\n\n"
            "A calm routine and gentle handling make travel much easier for sensitive kittens."
        ),
        "meta_title": "Travel Tips for Maine Coons | Frostline Coons",
        "meta_description": "Safe travel tips for Maine Coon kittens, from carrier training to stress‑free rides.",
        "keywords": "Maine Coon travel, kitten carrier training, cat travel tips",
        "cover_image": "images/hero_delivery.jpg"
    },
    {
        "title": "Playtime and Enrichment for Smart, Active Maine Coons",
        "excerpt": "Keep your Maine Coon engaged with enrichment ideas that match their intelligence and energy.",
        "content": (
            "Maine Coons are curious and intelligent. Daily interactive play keeps them mentally stimulated and physically fit.\n\n"
            "Rotate toys, use puzzle feeders, and offer climbing opportunities to prevent boredom.\n\n"
            "A consistent play routine strengthens the bond and supports healthy development."
        ),
        "meta_title": "Maine Coon Enrichment Ideas | Frostline Coons",
        "meta_description": "Best enrichment ideas for Maine Coons: play routines, puzzle toys, and climbing setups.",
        "keywords": "Maine Coon toys, cat enrichment, Maine Coon playtime",
        "cover_image": "images/jddh.jpg"
    },
    {
        "title": "Harness Training a Maine Coon: Step‑by‑Step",
        "excerpt": "Teach leash skills the gentle way with short sessions and positive reinforcement.",
        "content": (
            "Start with a well‑fitting harness and let your Maine Coon sniff and explore it first. "
            "Reward calm behavior with treats.\n\n"
            "Keep early sessions indoors and short. Once comfortable, introduce the leash and practice gentle guidance.\n\n"
            "When your kitten moves confidently, try quiet outdoor areas for short, supervised walks."
        ),
        "meta_title": "Maine Coon Harness Training | Frostline Coons",
        "meta_description": "Learn how to harness train a Maine Coon with gentle, step‑by‑step guidance.",
        "keywords": "Maine Coon harness, leash training cat, cat walking tips",
        "cover_image": "images/kanashi-7NcdSLcRTq8-unsplash.jpg"
    },
    {
        "title": "The First Week Home: A Calm Transition Plan",
        "excerpt": "Help your kitten settle in with a simple routine that builds trust and confidence.",
        "content": (
            "Begin with a quiet room that includes food, water, litter, and a cozy bed. "
            "Let your kitten explore at their own pace.\n\n"
            "Maintain a consistent feeding and play schedule to reduce stress. "
            "Short, gentle play sessions help build confidence.\n\n"
            "Within a week, most Maine Coons are ready to explore more of the home."
        ),
        "meta_title": "First Week with a Maine Coon Kitten | Frostline Coons",
        "meta_description": "A calm, practical plan for the first week with your Maine Coon kitten.",
        "keywords": "first week kitten, Maine Coon transition, new kitten tips",
        "cover_image": "images/hero_home.jpg"
    },
    {
        "title": "Maine Coon Vocalizations: Chirps, Trills, and Communication",
        "excerpt": "Understand the gentle sounds Maine Coons use to connect with their humans.",
        "content": (
            "Maine Coons often communicate with soft chirps and trills instead of loud meows. "
            "These sounds are friendly signals, not demands.\n\n"
            "You’ll hear different tones for greetings, attention, or play. "
            "With time, you’ll learn your kitten’s unique language.\n\n"
            "Responding calmly helps build trust and a strong bond."
        ),
        "meta_title": "Maine Coon Sounds & Communication | Frostline Coons",
        "meta_description": "Learn what Maine Coon chirps and trills mean and how they communicate with families.",
        "keywords": "Maine Coon vocalizations, cat chirps, Maine Coon sounds",
        "cover_image": "images/fluffy.jpg"
    },
    {
        "title": "Managing Shedding: Seasonal Coat Care",
        "excerpt": "Reduce shedding and keep the coat healthy through seasonal grooming.",
        "content": (
            "Maine Coons shed more during seasonal changes. Increase brushing frequency during spring and fall.\n\n"
            "Use a wide‑tooth comb first, then finish with a slicker brush for the topcoat. "
            "Keep sessions short and calm.\n\n"
            "A balanced diet and hydration also support a healthy coat and reduced shedding."
        ),
        "meta_title": "Maine Coon Shedding Guide | Frostline Coons",
        "meta_description": "Seasonal grooming tips to manage Maine Coon shedding and keep the coat healthy.",
        "keywords": "Maine Coon shedding, cat grooming tips, seasonal coat care",
        "cover_image": "images/health2.jpg"
    },
    {
        "title": "Ideal Home Setup: Litter, Scratching, and Climbing",
        "excerpt": "Create a home environment that matches a Maine Coon’s size and curiosity.",
        "content": (
            "Large litter boxes, sturdy scratching posts, and tall cat trees are essentials for Maine Coons. "
            "They need space to stretch and climb.\n\n"
            "Offer multiple scratching textures to protect furniture. "
            "Place climbing areas near windows for enrichment.\n\n"
            "A well‑set home environment keeps your cat confident and relaxed."
        ),
        "meta_title": "Best Home Setup for Maine Coons | Frostline Coons",
        "meta_description": "Build the ideal home setup for a Maine Coon with litter, scratching, and climbing essentials.",
        "keywords": "Maine Coon home setup, cat tree for Maine Coon, litter box size",
        "cover_image": "images/mission.jpg"
    },
    {
        "title": "Socializing Maine Coon Kittens with Kids",
        "excerpt": "Teach gentle handling and build a safe, positive relationship between kids and kittens.",
        "content": (
            "Start with short, supervised interactions. Teach children to use calm voices and gentle hands.\n\n"
            "Reward your kitten for calm behavior and give them plenty of breaks. "
            "A safe retreat space prevents overstimulation.\n\n"
            "With patience, Maine Coons often become wonderful family companions."
        ),
        "meta_title": "Maine Coon Kittens and Kids | Frostline Coons",
        "meta_description": "How to socialize Maine Coon kittens with kids safely and build a lasting bond.",
        "keywords": "Maine Coon kids, kitten socialization, family cat",
        "cover_image": "images/doherty.jpg"
    },
    {
        "title": "Nighttime Routine: Helping Your Kitten Sleep Through the Night",
        "excerpt": "A practical bedtime routine that supports calm nights for you and your kitten.",
        "content": (
            "End the day with a play‑and‑feed routine to help your kitten settle. "
            "A small meal after play encourages sleepiness.\n\n"
            "Keep the bedroom quiet and avoid overstimulation before bed. "
            "Consistency helps kittens learn the nighttime rhythm.\n\n"
            "Within a few weeks, most kittens adapt to a stable sleep routine."
        ),
        "meta_title": "Kitten Nighttime Routine | Frostline Coons",
        "meta_description": "Help your Maine Coon kitten sleep through the night with a gentle, consistent routine.",
        "keywords": "kitten sleep routine, Maine Coon nighttime, kitten bedtime tips",
        "cover_image": "images/hero_home.jpg"
    },
    {
        "title": "Choosing the Right Maine Coon Breeder: Red Flags and Green Flags",
        "excerpt": "Know what to look for in ethical breeding practices and transparent communication.",
        "content": (
            "A responsible breeder provides health records, clear communication, and a clean environment. "
            "They should be transparent about lineage and care routines.\n\n"
            "Red flags include rushed timelines, no vet documentation, or pressure to buy quickly.\n\n"
            "Choose a breeder who prioritizes the kitten’s welfare and long‑term support."
        ),
        "meta_title": "Choosing a Maine Coon Breeder | Frostline Coons",
        "meta_description": "Learn how to identify ethical Maine Coon breeders and avoid common red flags.",
        "keywords": "Maine Coon breeder, ethical breeders, buying a Maine Coon",
        "cover_image": "images/story.jpg"
    },
    {
        "title": "Maine Coon Lifespan and Senior Care",
        "excerpt": "Support your Maine Coon through every life stage with gentle, proactive care.",
        "content": (
            "Maine Coons can live long, healthy lives with proper nutrition and routine vet visits. "
            "As they age, they may need softer bedding and lower climbing options.\n\n"
            "Senior diets and joint support can help maintain comfort and mobility. "
            "Regular checkups are essential for early detection.\n\n"
            "A calm home environment and daily affection make the senior years rewarding."
        ),
        "meta_title": "Maine Coon Lifespan & Senior Care | Frostline Coons",
        "meta_description": "Learn how to care for Maine Coons as they age, including diet, comfort, and routine vet care.",
        "keywords": "Maine Coon lifespan, senior cat care, Maine Coon aging",
        "cover_image": "images/health.jpg"
    },
    {
        "title": "Water Play and Curiosity: Safe Ways to Encourage It",
        "excerpt": "Many Maine Coons love water — here’s how to make it fun and safe.",
        "content": (
            "Some Maine Coons are fascinated by water. Provide shallow bowls or trickling fountains for safe exploration.\n\n"
            "Never force water play. Let curiosity lead and reward gentle investigation with praise or treats.\n\n"
            "Short, supervised sessions keep water play safe and enjoyable."
        ),
        "meta_title": "Maine Coon Water Play | Frostline Coons",
        "meta_description": "Safe ways to encourage Maine Coon water play without stress or forcing.",
        "keywords": "Maine Coon water play, cat fountains, curious cats",
        "cover_image": "images/bee-felten-leidel-DkYlK2vyuZg-unsplash.jpg"
    },
    {
        "title": "Introducing Two Cats: A Gentle Maine Coon Plan",
        "excerpt": "A slow, scent‑first introduction method that builds confidence and reduces stress.",
        "content": (
            "Start with scent swapping and separate spaces for each cat. "
            "Allow them to explore each other’s space without direct contact.\n\n"
            "Use short, calm visual introductions with a barrier. "
            "Keep sessions positive and end on a good note.\n\n"
            "With patience, most cats adjust and learn to coexist peacefully."
        ),
        "meta_title": "Introducing Cats to a Maine Coon | Frostline Coons",
        "meta_description": "Learn a calm, step‑by‑step process for introducing a Maine Coon to another cat.",
        "keywords": "introducing cats, Maine Coon with other cats, cat introduction tips",
        "cover_image": "images/kanashi-h08T7bg4D5E-unsplash.jpg"
    },
    {
        "title": "Microchipping and Identification Essentials",
        "excerpt": "Protect your kitten with reliable identification and updated records.",
        "content": (
            "Microchipping is a permanent form of identification. "
            "Be sure to register the chip and keep contact info updated.\n\n"
            "Breakaway collars with ID tags can add an extra layer of safety. "
            "For indoor cats, microchipping is still strongly recommended.\n\n"
            "Simple identification steps can make a big difference if a cat is ever lost."
        ),
        "meta_title": "Microchipping Maine Coon Kittens | Frostline Coons",
        "meta_description": "Learn why microchipping and ID tags matter for Maine Coon kittens and how to keep records updated.",
        "keywords": "microchipping cats, Maine Coon identification, cat safety",
        "cover_image": "images/jack.jpg"
    },
    {
        "title": "How to Read a Vet Health Record for Your Kitten",
        "excerpt": "Understand the basics of vaccination records, deworming notes, and wellness checks.",
        "content": (
            "A kitten health record typically includes vaccination dates, deworming schedules, and vet exam notes. "
            "Ask your breeder to walk you through any unfamiliar terms.\n\n"
            "Look for consistent dates and clear documentation. "
            "Keep these records organized for future vet visits.\n\n"
            "Clear health records give you confidence in your kitten’s early care."
        ),
        "meta_title": "Reading Kitten Health Records | Frostline Coons",
        "meta_description": "Learn how to read and understand your Maine Coon kitten’s vet health records and vaccine schedule.",
        "keywords": "kitten health records, cat vaccines, Maine Coon vet care",
        "cover_image": "images/health.jpg"
    },
    {
        "title": "Maine Coon Personality Types: Finding the Right Match",
        "excerpt": "Every kitten is unique — here’s how to match personality with your household.",
        "content": (
            "Some Maine Coons are playful and bold, while others are calm and reserved. "
            "Ask about temperament observations and daily routines.\n\n"
            "Consider your household’s energy level. A quieter home may pair best with a gentle kitten, "
            "while active families often enjoy a playful companion.\n\n"
            "Matching personality ensures a smoother transition for both kitten and family."
        ),
        "meta_title": "Maine Coon Personality Match | Frostline Coons",
        "meta_description": "How to match Maine Coon kitten personalities to your home, lifestyle, and family.",
        "keywords": "Maine Coon personality, choosing a kitten, kitten temperament",
        "cover_image": "images/misty.jpg"
    },
    {
        "title": "Seasonal Care: Keeping Your Maine Coon Comfortable Year‑Round",
        "excerpt": "Adjust grooming, hydration, and indoor comfort across seasons.",
        "content": (
            "In warmer months, increase brushing to reduce shedding and keep your Maine Coon cool. "
            "Provide shade, fresh water, and air circulation.\n\n"
            "During colder months, maintain warmth and check for dry skin. "
            "Consistent grooming prevents mats from forming.\n\n"
            "Small seasonal adjustments keep your cat comfortable and healthy."
        ),
        "meta_title": "Seasonal Maine Coon Care | Frostline Coons",
        "meta_description": "Seasonal tips for Maine Coon care, including grooming, hydration, and comfort.",
        "keywords": "Maine Coon seasonal care, cat grooming tips, winter cat care",
        "cover_image": "images/hero_home.jpg"
    },
    {
        "title": "Indoor vs. Outdoor: Safe Options for Maine Coons",
        "excerpt": "Explore safe ways to provide outdoor time without sacrificing safety.",
        "content": (
            "Indoor living is the safest option for Maine Coons, but enrichment matters. "
            "Add window perches, climbing structures, and interactive play.\n\n"
            "If you want outdoor time, consider a secure catio or harness training. "
            "Supervised time outdoors reduces risk.\n\n"
            "A safe environment keeps your cat healthy while still meeting their curiosity."
        ),
        "meta_title": "Indoor vs Outdoor Maine Coon | Frostline Coons",
        "meta_description": "Learn safe indoor and outdoor options for Maine Coons, including catios and harness training.",
        "keywords": "indoor Maine Coon, catio, outdoor cat safety",
        "cover_image": "images/kanashi-7NcdSLcRTq8-unsplash.jpg"
    },
    {
        "title": "Understanding Maine Coon Play Styles and Toy Choices",
        "excerpt": "Pick toys that match your Maine Coon’s natural instincts and energy level.",
        "content": (
            "Maine Coons love interactive toys like feather wands, crinkle balls, and puzzle feeders. "
            "Rotate toys to keep interest high.\n\n"
            "Many enjoy chasing and climbing, so tall cat trees and tunnels are great additions.\n\n"
            "Daily play supports healthy weight and strong bonds with your family."
        ),
        "meta_title": "Maine Coon Toys & Play | Frostline Coons",
        "meta_description": "Best toy ideas and play styles for Maine Coons to keep them active and happy.",
        "keywords": "Maine Coon toys, cat play styles, interactive cat toys",
        "cover_image": "images/nono.jpg"
    },
    {
        "title": "Preparing for Delivery Day: From Carrier to First Cuddle",
        "excerpt": "A practical checklist for delivery day, whether your kitten arrives by ground or air.",
        "content": (
            "Prepare a quiet room with food, water, and litter before arrival. "
            "Have a comfortable carrier ready for safe transport home.\n\n"
            "Keep the environment calm and limit visitors on day one. "
            "Let your kitten explore at their own pace.\n\n"
            "The first cuddles come naturally once your kitten feels safe and settled."
        ),
        "meta_title": "Delivery Day Checklist | Frostline Coons",
        "meta_description": "Prepare for Maine Coon kitten delivery day with a calm, practical checklist.",
        "keywords": "kitten delivery day, Maine Coon arrival, new kitten checklist",
        "cover_image": "images/hero_delivery.jpg"
    },
    {
        "title": "Maine Coon Coat Care: Preventing Mats in Long Fur",
        "excerpt": "Learn how to prevent mats with the right tools, routine, and handling.",
        "content": (
            "Long coats are prone to matting around the chest, belly, and tail base. "
            "Brush gently in short sessions to avoid pulling.\n\n"
            "Use a wide‑tooth comb to detangle and follow with a slicker brush. "
            "Focus on friction areas during seasonal sheds.\n\n"
            "Consistent grooming keeps the coat comfortable and healthy."
        ),
        "meta_title": "Preventing Maine Coon Mats | Frostline Coons",
        "meta_description": "Prevent matting in Maine Coon coats with easy grooming tips and the right tools.",
        "keywords": "Maine Coon mats, grooming long hair cats, cat coat care",
        "cover_image": "images/health2.jpg"
    },
    {
        "title": "Best Litter Box Setup for Large Cats",
        "excerpt": "Large cats need large boxes — here’s how to set up a comfortable litter area.",
        "content": (
            "Maine Coons are bigger than most breeds, so standard litter boxes often feel cramped. "
            "Choose oversized boxes with low entry for easy access.\n\n"
            "Place boxes in quiet, low‑traffic areas and keep them very clean. "
            "Many cats prefer unscented clumping litter.\n\n"
            "A comfortable setup encourages consistent habits and reduces stress."
        ),
        "meta_title": "Litter Box Setup for Maine Coons | Frostline Coons",
        "meta_description": "Create the perfect litter box setup for large Maine Coon cats with practical tips.",
        "keywords": "large cat litter box, Maine Coon litter setup, litter box tips",
        "cover_image": "images/jddh.jpg"
    },
    {
        "title": "Maine Coon Vaccination Schedule: What to Know",
        "excerpt": "Understand the basics of kitten vaccines and why timing matters.",
        "content": (
            "Kittens receive a series of core vaccines during their first months. "
            "Your vet will provide a schedule based on age and health status.\n\n"
            "Follow recommended timelines to maintain protection during early development. "
            "Keep records organized for future visits.\n\n"
            "If you travel or board your cat, vaccines may be required by facilities."
        ),
        "meta_title": "Maine Coon Vaccine Schedule | Frostline Coons",
        "meta_description": "A simple overview of kitten vaccines and what to expect for Maine Coons.",
        "keywords": "kitten vaccines, Maine Coon vaccination, cat vaccine schedule",
        "cover_image": "images/health.jpg"
    },
    {
        "title": "How to Build Trust with a New Maine Coon Kitten",
        "excerpt": "Gentle routines and patience help your kitten feel safe and bonded.",
        "content": (
            "Trust grows through consistency. Offer food, play, and calm interaction at the same times each day.\n\n"
            "Use slow blinks and a soft voice. Let your kitten initiate contact rather than forcing cuddles.\n\n"
            "With a steady routine, most Maine Coons become deeply affectionate."
        ),
        "meta_title": "Building Trust with Maine Coon Kittens | Frostline Coons",
        "meta_description": "Learn how to build trust with a new Maine Coon kitten using calm routines and gentle handling.",
        "keywords": "Maine Coon kitten trust, bonding with kittens, new kitten tips",
        "cover_image": "images/luna.jpg"
    },
    {
        "title": "Maine Coon Shedding vs. Matting: What’s Normal?",
        "excerpt": "Understand the difference between normal shedding and coat issues that need attention.",
        "content": (
            "Shedding is normal for Maine Coons, especially during seasonal changes. "
            "Regular brushing keeps loose hair under control.\n\n"
            "Matting is different — it’s tangled fur that can pull on the skin. "
            "Focus on friction areas and use a comb to prevent mats.\n\n"
            "If mats form, handle them gently and consider professional grooming support."
        ),
        "meta_title": "Maine Coon Shedding vs Matting | Frostline Coons",
        "meta_description": "Learn the difference between normal Maine Coon shedding and coat matting issues.",
        "keywords": "Maine Coon shedding, cat matting, grooming tips",
        "cover_image": "images/fluffy.jpg"
    },
    {
        "title": "Maine Coon Playtime Schedule: How Much Is Enough?",
        "excerpt": "A realistic daily play routine that supports healthy energy and bonding.",
        "content": (
            "Aim for two to three short play sessions per day. "
            "Interactive play with wand toys helps satisfy hunting instincts.\n\n"
            "End sessions with a calm treat or meal to help your kitten settle.\n\n"
            "Consistent play reduces boredom and supports healthy behavior."
        ),
        "meta_title": "Maine Coon Playtime Routine | Frostline Coons",
        "meta_description": "How much playtime Maine Coon kittens need each day and how to structure sessions.",
        "keywords": "Maine Coon playtime, kitten play schedule, cat enrichment",
        "cover_image": "images/leo.jpg"
    },
    {
        "title": "Preparing Your Home for a Maine Coon’s First Winter",
        "excerpt": "Simple ways to keep your kitten cozy, hydrated, and comfortable in colder months.",
        "content": (
            "Keep bedding warm and away from drafts. "
            "Add cozy blankets and maintain a consistent indoor temperature.\n\n"
            "Monitor hydration in winter — heated homes can cause dryness. "
            "Fresh water and occasional wet food help balance it.\n\n"
            "Grooming remains important even in winter to keep the coat healthy."
        ),
        "meta_title": "Maine Coon Winter Care | Frostline Coons",
        "meta_description": "Winter care tips for Maine Coon kittens, including warmth, hydration, and coat care.",
        "keywords": "Maine Coon winter care, cat cold weather, kitten winter tips",
        "cover_image": "images/hero_home.jpg"
    },
    {
        "title": "Maine Coon Carrier Training for Stress‑Free Vet Visits",
        "excerpt": "Make the carrier a safe space with a few simple training steps.",
        "content": (
            "Leave the carrier out with soft bedding so your kitten can explore it freely. "
            "Use treats to create positive associations.\n\n"
            "Practice short, calm trips before vet visits. "
            "Keep the carrier stable and quiet during travel.\n\n"
            "Carrier training reduces stress and keeps vet days calm."
        ),
        "meta_title": "Maine Coon Carrier Training | Frostline Coons",
        "meta_description": "Tips for carrier training a Maine Coon kitten to reduce stress during vet visits.",
        "keywords": "cat carrier training, Maine Coon vet visit, kitten travel",
        "cover_image": "images/hero_delivery.jpg"
    },
    {
        "title": "How to Reserve a Maine Coon Kitten Online: A Step-by-Step Buyer Guide",
        "excerpt": "A clear, buyer-focused guide to reserving a Maine Coon kitten with confidence and zero surprises.",
        "content": (
            "If you are ready to bring home a Maine Coon kitten, a calm and transparent reservation process matters. "
            "The goal is to match the right kitten to the right home while keeping timing and expectations clear.\n\n"
            "## Step 1: Check availability and timing\n\n"
            "Start by reviewing which kittens are marked available and the timeline for homegoing. "
            "A good breeder shares realistic timing, not rushed promises.\n\n"
            "## Step 2: Share your home details\n\n"
            "Expect to answer questions about your household, lifestyle, and other pets. "
            "This helps ensure the kitten matches your energy level and routine.\n\n"
            "## Step 3: Review health and socialization notes\n\n"
            "Ask for vaccination records, wellness checks, and notes on personality. "
            "These details help you prepare the right care plan from day one.\n\n"
            "## Step 4: Choose delivery or pickup\n\n"
            "Decide between local pickup, ground transport, or airport pickup based on your location. "
            "Plan the handoff so your kitten arrives calm and secure.\n\n"
            "## Step 5: Prepare your home\n\n"
            "Set up a quiet starter room, food and water, and a large litter box. "
            "A stable routine helps your kitten settle quickly.\n\n"
            "A good reservation process should feel clear, respectful, and organized. "
            "When everything is laid out from the start, you can focus on the joy of welcoming your new companion."
        ),
        "meta_title": "How to Reserve a Maine Coon Kitten | Frostline Coons",
        "meta_description": "Step-by-step guide to reserving a Maine Coon kitten with clear timing, health details, and delivery planning.",
        "keywords": "reserve Maine Coon kitten, Maine Coon reservation, buy Maine Coon kitten",
        "cover_image": "https://source.unsplash.com/1600x900/?maine%20coon,cat&sig=1"
    },
    {
        "title": "Maine Coon Kittens in Ohio: Delivery, Airport Pickup, and Local Prep",
        "excerpt": "A practical Ohio-focused guide to timing, transport, and preparing your home for a Maine Coon kitten.",
        "content": (
            "Ohio families love Maine Coons for their calm temperament and family-friendly nature. "
            "Whether you are in Columbus, Cleveland, or Cincinnati, planning ahead makes the arrival smooth.\n\n"
            "## Plan the handoff that fits your city\n\n"
            "Some families prefer local pickup while others choose ground delivery or airport pickup. "
            "The right option depends on distance, schedule, and comfort level.\n\n"
            "## Build a cozy starter space\n\n"
            "Ohio winters can be chilly, so a warm starter room with soft bedding is ideal. "
            "Keep the litter box close and reduce noise for the first few days.\n\n"
            "## Focus on early routine\n\n"
            "Feeding at consistent times and short play sessions help a kitten feel safe. "
            "A steady routine matters more than a large space at first.\n\n"
            "## Expect a gentle transition\n\n"
            "Most Maine Coon kittens adapt quickly when the environment is calm. "
            "Give your kitten time to explore at their own pace.\n\n"
            "Ohio is a great place for a Maine Coon to thrive with indoor enrichment, window perches, and climbing areas. "
            "A simple, steady setup supports a confident start."
        ),
        "meta_title": "Ohio Maine Coon Kittens | Frostline Coons",
        "meta_description": "Ohio guide for Maine Coon kitten delivery, airport pickup, and home preparation tips.",
        "keywords": "Maine Coon kittens Ohio, Ohio Maine Coon breeder, Maine Coon delivery Ohio",
        "cover_image": "https://images.pexels.com/photos/7542156/pexels-photo-7542156.jpeg?cs=srgb&dl=pexels-kh-ali-li-7542156.jpg&fm=jpg"
    },
    {
        "title": "Maine Coon Kittens in Texas: Heat-Smart Care and Arrival Planning",
        "excerpt": "Texas-ready tips for transport, cooling, and a comfortable first week with your Maine Coon kitten.",
        "content": (
            "Texas homes are a great fit for Maine Coons when you plan for warm weather and indoor comfort. "
            "From Dallas to Houston to Austin, preparation makes the arrival easy.\n\n"
            "## Choose a low-stress arrival plan\n\n"
            "Coordinate pickup or delivery during cooler parts of the day. "
            "A calm handoff and stable carrier setup help reduce stress.\n\n"
            "## Keep the home cool and hydrated\n\n"
            "Offer fresh water in multiple locations and keep indoor temperatures steady. "
            "Long-haired cats do best when overheating is avoided.\n\n"
            "## Build vertical play space\n\n"
            "Texas homes often have room for tall cat trees and shelves. "
            "These let your kitten climb and feel confident without outdoor risks.\n\n"
            "## Start with a gentle routine\n\n"
            "A quiet starter room, small meals, and calm play sessions support a healthy transition. "
            "Consistency matters more than speed.\n\n"
            "With a heat-smart plan and a stable routine, Maine Coon kittens settle beautifully in Texas. "
            "Comfort and calm are the keys to a smooth first week."
        ),
        "meta_title": "Texas Maine Coon Kittens | Frostline Coons",
        "meta_description": "Texas guide for Maine Coon kitten delivery, heat-smart care, and arrival prep.",
        "keywords": "Maine Coon kittens Texas, Texas Maine Coon breeder, Maine Coon delivery Texas",
        "cover_image": "https://images.pexels.com/photos/35192272/pexels-photo-35192272.jpeg?cs=srgb&dl=pexels-mov-frame-288922282-35192272.jpg&fm=jpg"
    },
    {
        "title": "Maine Coon Kittens in Florida: Humidity, Coat Care, and Safe Transport",
        "excerpt": "Florida-specific guidance for transport timing, coat care, and a calm arrival.",
        "content": (
            "Florida’s warmth and humidity are manageable with the right indoor setup. "
            "Maine Coons thrive when their coat and hydration are supported.\n\n"
            "## Plan transport with comfort in mind\n\n"
            "Schedule delivery or airport pickup during cooler hours. "
            "Keep a breathable carrier and a soft, familiar blanket ready.\n\n"
            "## Manage coat comfort in humidity\n\n"
            "Regular brushing helps reduce trapped heat and keeps the coat airy. "
            "A clean coat helps your kitten stay comfortable in Florida’s climate.\n\n"
            "## Keep water accessible\n\n"
            "Multiple water bowls or a fountain encourage steady hydration. "
            "Hydration supports coat health and energy.\n\n"
            "## Ease into the first week\n\n"
            "Begin with a quiet room, small meals, and short play. "
            "A slow start leads to confident exploration.\n\n"
            "Florida homes can be perfect for Maine Coons with cool indoor air and enrichment. "
            "A calm arrival plan is the best first step."
        ),
        "meta_title": "Florida Maine Coon Kittens | Frostline Coons",
        "meta_description": "Florida guide for Maine Coon kitten delivery, coat care, and humidity-friendly setup.",
        "keywords": "Maine Coon kittens Florida, Florida Maine Coon breeder, Maine Coon delivery Florida",
        "cover_image": "https://images.pexels.com/photos/8942602/pexels-photo-8942602.jpeg?cs=srgb&dl=pexels-matteo-12850205-8942602.jpg&fm=jpg"
    },
    {
        "title": "Maine Coon Kittens in Tennessee: Family Homes, Temperament, and Pickup Options",
        "excerpt": "Tennessee-focused tips for choosing the right kitten and planning a calm arrival.",
        "content": (
            "Tennessee families love Maine Coons for their gentle temperament and playful nature. "
            "Whether you are near Nashville, Knoxville, or Memphis, preparation keeps things smooth.\n\n"
            "## Match personality to your household\n\n"
            "Ask about each kitten’s energy level and social style. "
            "A calm kitten can be ideal for quieter homes, while playful kittens suit active families.\n\n"
            "## Choose a pickup or delivery option\n\n"
            "Local pickup is great if you are close, while delivery helps when distance is longer. "
            "Either way, a calm handoff reduces stress.\n\n"
            "## Build a safe starter space\n\n"
            "A quiet room with food, water, litter, and a cozy bed helps a kitten settle. "
            "Keep the space calm for the first few days.\n\n"
            "## Support gentle bonding\n\n"
            "Short play sessions and predictable routines help trust grow quickly. "
            "Most Maine Coons respond well to consistent care.\n\n"
            "With a thoughtful arrival plan and a stable routine, Tennessee homes are a wonderful fit. "
            "The right preparation makes the transition feel easy."
        ),
        "meta_title": "Tennessee Maine Coon Kittens | Frostline Coons",
        "meta_description": "Tennessee guide to Maine Coon kitten temperament, pickup options, and home prep.",
        "keywords": "Maine Coon kittens Tennessee, Tennessee Maine Coon breeder, Maine Coon delivery Tennessee",
        "cover_image": "https://images.pexels.com/photos/31566261/pexels-photo-31566261.jpeg?cs=srgb&dl=pexels-valeriya-310343202-31566261.jpg&fm=jpg"
    },
    {
        "title": "Maine Coon Kittens in Kentucky: A Practical Buying Checklist",
        "excerpt": "A Kentucky buyer’s checklist for health records, delivery planning, and the first week home.",
        "content": (
            "Kentucky families often look for a calm, affectionate breed that fits a family home. "
            "Maine Coons are a strong match when the process is clear and organized.\n\n"
            "## Review health documentation\n\n"
            "Ask for vaccination notes, wellness checks, and a clear care summary. "
            "These records help you plan the first vet visit.\n\n"
            "## Confirm timing and transport\n\n"
            "Whether you choose pickup or delivery, align the schedule with your family’s routine. "
            "A calm arrival leads to a smoother transition.\n\n"
            "## Prepare the starter essentials\n\n"
            "Set up a quiet room, a large litter box, and a few toys. "
            "A simple environment feels safer than a busy one.\n\n"
            "## Build early bonding habits\n\n"
            "Short, gentle play sessions help trust grow. "
            "Let your kitten explore without pressure.\n\n"
            "Kentucky homes can be an excellent fit for Maine Coons. "
            "A clear checklist keeps the process stress-free."
        ),
        "meta_title": "Kentucky Maine Coon Kittens | Frostline Coons",
        "meta_description": "Kentucky guide to buying a Maine Coon kitten, including health checks and arrival prep.",
        "keywords": "Maine Coon kittens Kentucky, Kentucky Maine Coon breeder, Maine Coon delivery Kentucky",
        "cover_image": "https://images.pexels.com/photos/33008526/pexels-photo-33008526.jpeg?cs=srgb&dl=pexels-nadiye-odabasi-388149131-33008526.jpg&fm=jpg"
    },
    {
        "title": "Maine Coon Kittens in New York: Apartment Living and Enrichment",
        "excerpt": "How to raise a Maine Coon in New York with smart space planning and daily enrichment.",
        "content": (
            "New York homes and apartments can still be perfect for a Maine Coon with the right setup. "
            "The key is vertical space and a consistent routine.\n\n"
            "## Maximize vertical space\n\n"
            "Tall cat trees and wall shelves provide climbing outlets without needing a large footprint. "
            "Window perches add light and daily stimulation.\n\n"
            "## Keep a calm starter zone\n\n"
            "A quiet starter room helps your kitten settle before exploring the whole apartment. "
            "Small spaces feel safer at first.\n\n"
            "## Choose a low-stress arrival option\n\n"
            "Airport pickup or ground delivery can work well in the city if scheduled carefully. "
            "Plan the handoff for a calm, low-traffic time.\n\n"
            "## Build a steady routine\n\n"
            "Consistent feeding and play times help your kitten feel secure in a busy environment. "
            "Routine is your best tool in a fast-paced city.\n\n"
            "New York can be a wonderful home for a Maine Coon with the right enrichment. "
            "Vertical space and calm routines are the winning formula."
        ),
        "meta_title": "New York Maine Coon Kittens | Frostline Coons",
        "meta_description": "New York guide to raising Maine Coon kittens in apartments with enrichment and smart space planning.",
        "keywords": "Maine Coon kittens New York, New York Maine Coon breeder, Maine Coon apartment living",
        "cover_image": "https://images.pexels.com/photos/8145383/pexels-photo-8145383.jpeg?cs=srgb&dl=pexels-odin-8145383.jpg&fm=jpg"
    },
    {
        "title": "What to Ask Before You Reserve a Maine Coon Kitten",
        "excerpt": "A buyer-focused question list that protects your family and your future kitten.",
        "content": (
            "A great reservation experience starts with clear, respectful communication. "
            "The right questions help you understand care, timing, and the kitten’s personality.\n\n"
            "## Ask about health checks and records\n\n"
            "Request vaccination schedules, wellness checks, and any genetic screening notes. "
            "Clear documentation shows consistent care.\n\n"
            "## Ask about daily routine\n\n"
            "Learn what the kitten eats, how often they play, and their sleep schedule. "
            "Matching routines makes the transition smoother.\n\n"
            "## Ask about socialization\n\n"
            "Find out how the kitten responds to handling, kids, and other pets. "
            "This helps you choose the right match.\n\n"
            "## Ask about delivery and pickup\n\n"
            "Clarify transport options and timelines so you can plan ahead. "
            "A thoughtful handoff helps reduce stress.\n\n"
            "The best breeders welcome questions and answer with care. "
            "A calm, transparent process is the foundation of a great match."
        ),
        "meta_title": "Questions Before Reserving a Maine Coon | Frostline Coons",
        "meta_description": "Top questions to ask before reserving a Maine Coon kitten, from health checks to socialization.",
        "keywords": "reserve Maine Coon kitten, questions to ask breeder, Maine Coon buyer guide",
        "cover_image": "https://source.unsplash.com/1600x900/?maine%20coon,kitten&sig=2"
    },
    {
        "title": "Health Checks for Maine Coon Kittens: What Responsible Breeders Provide",
        "excerpt": "A clear overview of health checks and care details you should expect before bringing a kitten home.",
        "content": (
            "Health checks are about more than a single vet visit. "
            "They include consistent records, vaccines, and a clear care summary.\n\n"
            "## Vaccination and parasite prevention\n\n"
            "Your kitten should have age-appropriate vaccines and deworming notes. "
            "A written schedule helps you plan future care.\n\n"
            "## Wellness checks and observations\n\n"
            "Breeders should share notes on appetite, energy, and overall behavior. "
            "These details help your vet continue care smoothly.\n\n"
            "## Transparent documentation\n\n"
            "Clear records show how the kitten was cared for and monitored. "
            "This builds confidence and reduces uncertainty.\n\n"
            "## Ongoing support\n\n"
            "A responsible breeder remains available for questions after the kitten goes home. "
            "That support can make the first weeks easier.\n\n"
            "Good health records are a sign of good care. "
            "They protect your kitten and give your family peace of mind."
        ),
        "meta_title": "Maine Coon Kitten Health Checks | Frostline Coons",
        "meta_description": "What health checks and records you should expect before buying or reserving a Maine Coon kitten.",
        "keywords": "Maine Coon health checks, kitten vet records, responsible breeder",
        "cover_image": "https://images.pexels.com/photos/35494087/pexels-photo-35494087.jpeg?cs=srgb&dl=pexels-alexander-gray-1924221403-35494087.jpg&fm=jpg"
    },
    {
        "title": "Adoption Journey Explained: 4 Steps From Inquiry to Home",
        "excerpt": "A simple four-step adoption journey so you know exactly what to expect.",
        "content": (
            "A clear adoption journey makes the process calm and predictable. "
            "Here is a simple four-step flow that keeps everything organized.\n\n"
            "## Step 1: Inquiry and fit\n\n"
            "Share your household details and preferences so you can be matched thoughtfully. "
            "This helps align personality and lifestyle.\n\n"
            "## Step 2: Reservation and planning\n\n"
            "Once a match is confirmed, reserve your kitten and confirm timing. "
            "This step keeps expectations clear.\n\n"
            "## Step 3: Preparation\n\n"
            "Set up a starter room, gather supplies, and review care notes. "
            "Preparation makes the first week feel easy.\n\n"
            "## Step 4: Homecoming\n\n"
            "Choose pickup or delivery and complete the handoff calmly. "
            "A steady routine helps your kitten settle in quickly.\n\n"
            "The adoption journey should feel supportive and clear. "
            "A simple structure helps everyone feel confident."
        ),
        "meta_title": "Maine Coon Adoption Journey | Frostline Coons",
        "meta_description": "Four clear steps from inquiry to home for adopting a Maine Coon kitten.",
        "keywords": "Maine Coon adoption journey, reserve kitten, Maine Coon process",
        "cover_image": "https://source.unsplash.com/1600x900/?long%20haired%20cat&sig=3"
    },
    {
        "title": "Delivery vs Airport Pickup: Choosing the Safest Option for Your Kitten",
        "excerpt": "Compare delivery and airport pickup so you can choose the safest, calmest option.",
        "content": (
            "Choosing how your kitten arrives is a big decision. "
            "The best option depends on distance, timing, and your comfort level.\n\n"
            "## Ground delivery\n\n"
            "Ground transport can be a calm option for shorter distances. "
            "It allows for steady, careful travel without airport changes.\n\n"
            "## Airport pickup\n\n"
            "Airport pickup works well for long distances when timing is coordinated. "
            "A quick, calm handoff keeps stress low.\n\n"
            "## Consider your schedule\n\n"
            "Choose an option that fits your availability so the handoff is smooth. "
            "Your kitten benefits from a calm, unhurried transition.\n\n"
            "## Plan the first hour home\n\n"
            "Bring a quiet carrier, water, and a soft blanket. "
            "A gentle first hour makes a big difference.\n\n"
            "Both options can be safe with proper planning. "
            "The goal is a calm, secure arrival."
        ),
        "meta_title": "Delivery vs Airport Pickup for Maine Coons | Frostline Coons",
        "meta_description": "Compare Maine Coon kitten delivery and airport pickup to choose the safest option.",
        "keywords": "Maine Coon delivery, airport pickup kitten, kitten transport",
        "cover_image": "https://images.pexels.com/photos/10626405/pexels-photo-10626405.jpeg?cs=srgb&dl=pexels-just-dry-10626405.jpg&fm=jpg"
    },
    {
        "title": "Preparing a Large Breed Kitten: Space Planning for Maine Coons",
        "excerpt": "A practical home setup guide for large-breed kittens that need room to climb and stretch.",
        "content": (
            "Maine Coons are large-breed cats with a strong need for space and vertical movement. "
            "Planning the environment early prevents stress and keeps behavior positive.\n\n"
            "## Choose large essentials\n\n"
            "Oversized litter boxes, sturdy scratchers, and tall cat trees are must-haves. "
            "These basics match their size from the start.\n\n"
            "## Create vertical routes\n\n"
            "Shelves, perches, and cat trees give your kitten safe climbing options. "
            "Vertical space can matter more than floor space.\n\n"
            "## Build a calm starter room\n\n"
            "Start small with a quiet room and expand access slowly. "
            "This keeps the transition smooth and controlled.\n\n"
            "## Keep routines consistent\n\n"
            "Set feeding and play times so your kitten feels secure. "
            "Consistency builds confidence.\n\n"
            "A thoughtful setup makes a large-breed kitten feel at home quickly. "
            "Space planning is one of the best gifts you can give."
        ),
        "meta_title": "Large Breed Kitten Setup | Frostline Coons",
        "meta_description": "Home setup guide for large-breed Maine Coon kittens with space, climbing, and routine tips.",
        "keywords": "large breed kitten setup, Maine Coon home, Maine Coon space needs",
        "cover_image": "https://source.unsplash.com/1600x900/?cat%20family&sig=4"
    },
    {
        "title": "Maine Coon Temperament With Kids: Building Gentle Bonds",
        "excerpt": "How to create safe, affectionate relationships between children and Maine Coon kittens.",
        "content": (
            "Maine Coons are known for a calm, affectionate nature that often pairs well with kids. "
            "The best outcomes come from gentle handling and predictable routines.\n\n"
            "## Teach calm interaction\n\n"
            "Show children how to use quiet voices and soft hands. "
            "Short, supervised visits build trust quickly.\n\n"
            "## Create a safe retreat\n\n"
            "Give your kitten a quiet space where they can rest. "
            "This prevents overstimulation and keeps interactions positive.\n\n"
            "## Use play as bonding\n\n"
            "Wand toys and gentle games are ideal for kids. "
            "Play creates positive associations without rough handling.\n\n"
            "## Keep routines steady\n\n"
            "Consistent feeding and play times help your kitten feel secure. "
            "Security leads to affectionate behavior.\n\n"
            "With calm guidance, Maine Coons often become wonderful family companions. "
            "Gentle routines make the bond stronger."
        ),
        "meta_title": "Maine Coon Kittens and Kids | Frostline Coons",
        "meta_description": "Tips for raising Maine Coon kittens with kids and creating gentle, safe bonds.",
        "keywords": "Maine Coon kids, family cat, Maine Coon temperament",
        "cover_image": "https://images.pexels.com/photos/16371569/pexels-photo-16371569.jpeg?cs=srgb&dl=pexels-anastasia-dervene-498671576-16371569.jpg&fm=jpg"
    },
    {
        "title": "Male vs Female Maine Coons: Personality Differences and Home Fit",
        "excerpt": "A balanced look at common temperament trends so you can choose the right fit.",
        "content": (
            "Every kitten is unique, but there are gentle trends that can help you decide. "
            "The best choice is the one that fits your lifestyle and home energy.\n\n"
            "## Male temperament trends\n\n"
            "Males are often described as playful, social, and easygoing. "
            "Many enjoy interactive play and frequent attention.\n\n"
            "## Female temperament trends\n\n"
            "Females can be a bit more independent while still affectionate. "
            "They often form strong bonds once trust is built.\n\n"
            "## Focus on individual personality\n\n"
            "Ask about each kitten’s behavior, energy, and social style. "
            "Personality matters more than gender alone.\n\n"
            "## Match to your routine\n\n"
            "Choose the kitten that best fits your daily rhythm and household. "
            "A good match makes the transition smoother.\n\n"
            "Gender can help guide your choice, but personality should lead the decision. "
            "A thoughtful match creates long-term harmony."
        ),
        "meta_title": "Male vs Female Maine Coons | Frostline Coons",
        "meta_description": "Compare male and female Maine Coon temperament trends to choose the right fit.",
        "keywords": "male vs female Maine Coon, Maine Coon personality, choosing a kitten",
        "cover_image": "https://source.unsplash.com/1600x900/?cat%20grooming&sig=5"
    },
    {
        "title": "Socialization in the First 12 Weeks: Why It Matters",
        "excerpt": "Early socialization shapes confidence, bonding, and long-term behavior.",
        "content": (
            "The first 12 weeks are a critical window for building confidence and trust. "
            "Gentle handling and positive exposure shape long-term behavior.\n\n"
            "## Handling and touch\n\n"
            "Regular, gentle handling helps kittens feel safe with people. "
            "This creates calm, affectionate adults.\n\n"
            "## Sounds and environment\n\n"
            "Exposure to normal household sounds helps reduce fear later. "
            "Consistency is more important than intensity.\n\n"
            "## People and routines\n\n"
            "Meeting different people and routines helps kittens adapt. "
            "A predictable rhythm keeps stress low.\n\n"
            "## Carry socialization forward\n\n"
            "Continue gentle exposure after your kitten comes home. "
            "Short, positive experiences keep confidence growing.\n\n"
            "Good socialization is one of the best gifts you can give a Maine Coon. "
            "It supports trust, calmness, and deep bonding."
        ),
        "meta_title": "Maine Coon Socialization Guide | Frostline Coons",
        "meta_description": "Why early socialization matters and how it shapes Maine Coon kitten behavior.",
        "keywords": "Maine Coon socialization, kitten socialization, early handling",
        "cover_image": "https://source.unsplash.com/1600x900/?cat%20carrier&sig=6"
    },
    {
        "title": "Feeding Plan for the First Year: Maine Coon Growth Without Overfeeding",
        "excerpt": "A first-year feeding guide focused on steady growth, joint support, and healthy energy.",
        "content": (
            "Maine Coons grow slowly, so the goal is steady development rather than rapid weight gain. "
            "A balanced feeding plan supports bone health and energy.\n\n"
            "## Choose kitten-specific nutrition\n\n"
            "Look for high-quality protein and balanced minerals. "
            "Large-breed kittens benefit from steady, controlled growth.\n\n"
            "## Keep a consistent schedule\n\n"
            "Smaller meals throughout the day help digestion and energy. "
            "A consistent schedule also supports routine.\n\n"
            "## Monitor body condition\n\n"
            "Check for steady weight gain without excess. "
            "Ask your vet if you are unsure about portions.\n\n"
            "## Hydration matters\n\n"
            "Fresh water and occasional wet food support hydration. "
            "Hydration also helps coat and skin health.\n\n"
            "A steady, balanced feeding plan helps your Maine Coon grow strong and healthy. "
            "Consistency is the most important ingredient."
        ),
        "meta_title": "Maine Coon First-Year Feeding Plan | Frostline Coons",
        "meta_description": "Feeding plan for Maine Coon kittens focused on steady growth and healthy development.",
        "keywords": "Maine Coon feeding plan, kitten nutrition, large breed kitten food",
        "cover_image": "https://source.unsplash.com/1600x900/?cat%20play&sig=7"
    },
    {
        "title": "Grooming Plan for Busy Families: Keep the Coat Healthy Year-Round",
        "excerpt": "A simple, realistic grooming routine that fits busy schedules and long coats.",
        "content": (
            "Long coats can stay healthy with a simple, consistent routine. "
            "Short, calm sessions work better than long grooming marathons.\n\n"
            "## Focus on friction areas\n\n"
            "Chest, belly, and behind the legs are the most common spots for tangles. "
            "A quick daily check prevents mats from forming.\n\n"
            "## Use the right tools\n\n"
            "Start with a wide-tooth comb and finish with a slicker brush. "
            "Gentle pressure keeps grooming stress-free.\n\n"
            "## Keep sessions short\n\n"
            "Five to ten minutes a few times a week is usually enough. "
            "Consistency matters more than length.\n\n"
            "## Add a calm reward\n\n"
            "Treats or quiet praise help your kitten associate grooming with comfort. "
            "This makes future sessions easier.\n\n"
            "Busy families can maintain a healthy coat with a steady, simple routine. "
            "Small habits make a big difference."
        ),
        "meta_title": "Maine Coon Grooming Routine for Busy Families | Frostline Coons",
        "meta_description": "A simple grooming plan to keep Maine Coon coats healthy without long sessions.",
        "keywords": "Maine Coon grooming routine, long hair cat grooming, coat care",
        "cover_image": "https://images.pexels.com/photos/8942614/pexels-photo-8942614.jpeg?cs=srgb&dl=pexels-matteo-12850205-8942614.jpg&fm=jpg"
    },
    {
        "title": "Introducing a Maine Coon to a Resident Cat: A Calm Timeline",
        "excerpt": "A calm, structured timeline for introducing a new kitten to your resident cat.",
        "content": (
            "Introducing cats is all about patience and slow steps. "
            "A calm timeline reduces stress for both pets.\n\n"
            "## Start with scent swapping\n\n"
            "Let each cat explore the other’s scent using blankets or toys. "
            "This builds familiarity without pressure.\n\n"
            "## Use a visual barrier\n\n"
            "A baby gate or cracked door allows safe visual contact. "
            "Keep sessions short and positive.\n\n"
            "## Increase time gradually\n\n"
            "Extend sessions only when both cats remain calm. "
            "Rushing can create setbacks.\n\n"
            "## Support each cat’s confidence\n\n"
            "Provide separate resources like litter boxes and food. "
            "This prevents competition while they adjust.\n\n"
            "A slow, calm introduction leads to the best long-term relationship. "
            "Patience is the key to harmony."
        ),
        "meta_title": "Introduce a Maine Coon to Another Cat | Frostline Coons",
        "meta_description": "Step-by-step timeline for introducing a Maine Coon kitten to a resident cat.",
        "keywords": "introducing cats, Maine Coon and other cats, cat introduction timeline",
        "cover_image": "https://source.unsplash.com/1600x900/?cat%20portrait&sig=8"
    },
    {
        "title": "The Best Toys and Enrichment for Intelligent Maine Coons",
        "excerpt": "Keep Maine Coons engaged with smart play, puzzle feeders, and climbing challenges.",
        "content": (
            "Maine Coons are intelligent and curious, so enrichment is essential. "
            "Variety keeps boredom away and supports healthy energy.\n\n"
            "## Interactive play\n\n"
            "Wand toys, feather teasers, and chase games are excellent daily options. "
            "Short sessions throughout the day work best.\n\n"
            "## Puzzle feeders\n\n"
            "Food puzzles turn mealtime into mental enrichment. "
            "This slows eating and engages the mind.\n\n"
            "## Climbing and perches\n\n"
            "Vertical space lets Maine Coons explore safely indoors. "
            "Tall trees and shelves are great for large breeds.\n\n"
            "## Rotate and refresh\n\n"
            "Rotate toys weekly to keep interest high. "
            "New textures and sounds keep play exciting.\n\n"
            "A thoughtful enrichment plan keeps Maine Coons happy and confident. "
            "Daily play is one of the best investments you can make."
        ),
        "meta_title": "Best Toys for Maine Coons | Frostline Coons",
        "meta_description": "Best toys and enrichment ideas for Maine Coons, including puzzles and climbing setups.",
        "keywords": "Maine Coon toys, cat enrichment, puzzle feeders",
        "cover_image": "https://source.unsplash.com/1600x900/?cat%20sleeping&sig=9"
    },
    {
        "title": "Understanding a Breeder Contract and Health Guarantee (Plain-English Guide)",
        "excerpt": "A simple, buyer-friendly overview of what breeder contracts and guarantees typically include.",
        "content": (
            "A breeder contract should feel clear and reasonable, not confusing. "
            "It exists to protect both your kitten and the breeder’s standards.\n\n"
            "## Health guarantees\n\n"
            "Health guarantees often outline a time period for initial vet checks. "
            "They usually explain what happens if a serious issue is discovered.\n\n"
            "## Care expectations\n\n"
            "Contracts may require routine vet care, proper nutrition, and safe housing. "
            "These expectations are common and support the kitten’s long-term health.\n\n"
            "## Return and rehome policies\n\n"
            "Some breeders ask to be contacted if rehoming is ever needed. "
            "This keeps the kitten safe and accounted for.\n\n"
            "## Ask for clarity\n\n"
            "If any section is unclear, ask questions before you sign. "
            "A responsible breeder will explain everything in plain language.\n\n"
            "A good contract should feel straightforward and fair. "
            "Clear expectations help create a smooth adoption experience."
        ),
        "meta_title": "Breeder Contract and Health Guarantee Guide | Frostline Coons",
        "meta_description": "Plain-English guide to breeder contracts and health guarantees for Maine Coon kittens.",
        "keywords": "Maine Coon contract, health guarantee, buying a Maine Coon kitten",
        "cover_image": "https://source.unsplash.com/1600x900/?cat%20home&sig=10"
    },
    {
        "title": "Maine Coon Kitten Buyer Checklist: 10 Things to Confirm",
        "excerpt": "A buyer-ready checklist to confirm health, socialization, and delivery details before you reserve.",
        "content": (
            "A clear checklist helps you move from interest to confident purchase. "
            "Use this list to confirm the essentials before you reserve.\n\n"
            "## Health records and wellness notes\n\n"
            "Confirm vaccinations, deworming, and wellness observations are documented. "
            "Clear records show consistent care.\n\n"
            "## Temperament and socialization\n\n"
            "Ask how the kitten responds to handling, people, and other pets. "
            "Personality fit matters as much as appearance.\n\n"
            "## Food and routine\n\n"
            "Learn what the kitten is currently eating and the daily schedule. "
            "Matching routines eases the transition.\n\n"
            "## Delivery or pickup plan\n\n"
            "Clarify timing, handoff details, and what to bring on arrival day. "
            "A smooth handoff reduces stress.\n\n"
            "A simple checklist makes the process feel organized and calm. "
            "Clear details lead to a confident homecoming."
        ),
        "meta_title": "Maine Coon Kitten Buyer Checklist | Frostline Coons",
        "meta_description": "Buyer checklist for reserving a Maine Coon kitten, covering health, socialization, and delivery.",
        "keywords": "Maine Coon buyer checklist, reserve Maine Coon kitten, buy Maine Coon",
        "cover_image": "https://source.unsplash.com/1600x900/?maine%20coon,kitten&sig=11"
    },
    {
        "title": "When Are Maine Coon Kittens Ready to Go Home?",
        "excerpt": "A calm, practical guide to readiness, socialization, and planning the right homegoing time.",
        "content": (
            "Homegoing timing depends on readiness, not just age. "
            "The goal is a confident kitten who eats well, uses the litter box, and handles routine life.\n\n"
            "## Physical readiness\n\n"
            "Kittens should be steady on solid food and gaining weight consistently. "
            "A healthy routine signals they are ready for a new home.\n\n"
            "## Social confidence\n\n"
            "Well-socialized kittens respond calmly to gentle handling and new sounds. "
            "Confidence now makes transitions easier later.\n\n"
            "## Health checks complete\n\n"
            "Vaccinations and wellness checks should be documented and up to date. "
            "Clear records help your vet continue care.\n\n"
            "## Plan the transition\n\n"
            "A quiet starter room and familiar food help your kitten settle quickly. "
            "Preparation is a key part of readiness.\n\n"
            "A responsible timeline prioritizes your kitten’s health and confidence. "
            "That patience creates a smoother, calmer homecoming."
        ),
        "meta_title": "When Maine Coon Kittens Go Home | Frostline Coons",
        "meta_description": "Learn when Maine Coon kittens are ready to go home, including health and socialization readiness.",
        "keywords": "when do Maine Coon kittens go home, Maine Coon homegoing, kitten readiness",
        "cover_image": "https://source.unsplash.com/1600x900/?cat%20nap&sig=12"
    },
    {
        "title": "Room-by-Room Kitten Proofing for Maine Coons",
        "excerpt": "A practical, room-by-room guide to making your home safe for a curious Maine Coon kitten.",
        "content": (
            "Maine Coon kittens are bold explorers, so a room-by-room check makes the home safer. "
            "Focus on reducing hazards while keeping the space engaging.\n\n"
            "## Living room\n\n"
            "Secure cords, remove small swallowable items, and stabilize tall furniture. "
            "Add a sturdy scratcher to redirect attention.\n\n"
            "## Kitchen and dining\n\n"
            "Keep counters clear of food scraps and secure trash lids. "
            "Block access to tight gaps behind appliances.\n\n"
            "## Bedrooms and bathrooms\n\n"
            "Close toilet lids, remove strings or small objects, and keep medications secured. "
            "Offer a quiet resting place for downtime.\n\n"
            "## Stairways and balconies\n\n"
            "Use baby gates if needed and avoid open balcony access. "
            "Safety comes first for a climbing kitten.\n\n"
            "A quick room-by-room check prevents common accidents. "
            "It also gives your kitten a calmer, safer environment to explore."
        ),
        "meta_title": "Kitten Proofing for Maine Coons | Frostline Coons",
        "meta_description": "Room-by-room kitten proofing tips for Maine Coon homes, focused on safety and calm transitions.",
        "keywords": "kitten proofing, Maine Coon home safety, kitten proofing checklist",
        "cover_image": "https://source.unsplash.com/1600x900/?cat%20window&sig=13"
    },
    {
        "title": "Maine Coon Training Basics: Litter, Scratching, and Recall",
        "excerpt": "Simple training foundations that build good habits without stress.",
        "content": (
            "Training a Maine Coon kitten is about consistency, not force. "
            "Short, positive sessions build trust and reliable habits.\n\n"
            "## Litter habits\n\n"
            "Use a large, low-entry litter box and keep it very clean. "
            "Most Maine Coons learn quickly with a consistent location.\n\n"
            "## Scratching routines\n\n"
            "Offer multiple scratching textures and place them near favorite areas. "
            "Reward your kitten for using the scratcher.\n\n"
            "## Gentle recall\n\n"
            "Use the kitten’s name and a treat to build a positive response. "
            "Short sessions keep training fun.\n\n"
            "## Keep it positive\n\n"
            "Avoid punishment and focus on gentle redirection. "
            "Positive reinforcement builds lifelong trust.\n\n"
            "Simple training basics make daily life easier for both kitten and family. "
            "Calm consistency is the secret."
        ),
        "meta_title": "Maine Coon Training Basics | Frostline Coons",
        "meta_description": "Training basics for Maine Coon kittens: litter, scratching, and gentle recall.",
        "keywords": "Maine Coon training, kitten training, litter training Maine Coon",
        "cover_image": "https://images.pexels.com/photos/96973/pexels-photo-96973.jpeg?cs=srgb&dl=pexels-dan-wheeler-96973.jpg&fm=jpg"
    },
    {
        "title": "Understanding Maine Coon Registration and Paperwork",
        "excerpt": "A plain-language guide to registration, pedigrees, and what the paperwork means.",
        "content": (
            "Registration paperwork helps document lineage and recordkeeping. "
            "It is useful for families who value pedigree transparency.\n\n"
            "## What registration shows\n\n"
            "Registration typically lists lineage details and breeder information. "
            "It is not a health guarantee, but it does offer clarity.\n\n"
            "## How to read the paperwork\n\n"
            "Ask about any unfamiliar terms and confirm the kitten’s registered name. "
            "Keep documents organized for future reference.\n\n"
            "## Why it matters to buyers\n\n"
            "For many buyers, registration adds confidence in lineage and breeding standards. "
            "It is one more layer of transparency.\n\n"
            "If registration matters to you, ask about it early. "
            "Clear paperwork supports a smooth adoption experience."
        ),
        "meta_title": "Maine Coon Registration Guide | Frostline Coons",
        "meta_description": "Plain-language guide to Maine Coon registration, pedigrees, and paperwork.",
        "keywords": "Maine Coon registration, TICA Maine Coon, CFA Maine Coon",
        "cover_image": "https://images.pexels.com/photos/31566260/pexels-photo-31566260.jpeg?cs=srgb&dl=pexels-valeriya-310343202-31566260.jpg&fm=jpg"
    },
    {
        "title": "Why Maine Coons Need Large Litter Boxes (And How to Set Them Up)",
        "excerpt": "Size matters for comfort and clean habits. Here is a simple setup guide.",
        "content": (
            "Maine Coons are larger than most cats, so standard litter boxes can feel cramped. "
            "A proper setup supports consistent habits and reduces mess.\n\n"
            "## Choose the right size\n\n"
            "Look for oversized boxes with low entry and high sides. "
            "Large boxes reduce accidents and stress.\n\n"
            "## Pick a low-dust litter\n\n"
            "Unscented, fine-grain litter is usually best for kittens. "
            "Keep the box clean to encourage use.\n\n"
            "## Place boxes strategically\n\n"
            "Quiet, accessible locations work best. "
            "Avoid noisy areas or tight corners.\n\n"
            "## Keep a simple routine\n\n"
            "Daily scooping and weekly refreshes keep things clean. "
            "Consistency builds good habits.\n\n"
            "A comfortable litter setup is one of the easiest ways to reduce stress. "
            "It helps your kitten feel secure from day one."
        ),
        "meta_title": "Large Litter Box Setup for Maine Coons | Frostline Coons",
        "meta_description": "Why Maine Coons need large litter boxes and how to set up a comfortable litter area.",
        "keywords": "large litter box Maine Coon, Maine Coon litter setup, cat litter box size",
        "cover_image": "https://images.pexels.com/photos/5701041/pexels-photo-5701041.jpeg?cs=srgb&dl=pexels-arkadyes-5701041.jpg&fm=jpg"
    },
    {
        "title": "Grooming Tools Checklist for Maine Coons",
        "excerpt": "The essential tools for long coats, plus how to use them without stress.",
        "content": (
            "The right tools make grooming calmer and more effective. "
            "A small, consistent routine is better than long sessions.\n\n"
            "## Wide-tooth comb\n\n"
            "Use a comb to detangle the undercoat and prevent mats. "
            "Work slowly through friction areas.\n\n"
            "## Slicker brush\n\n"
            "A slicker brush smooths the topcoat and removes loose hair. "
            "Use gentle pressure and short strokes.\n\n"
            "## Grooming wipes\n\n"
            "Wipes are helpful for quick cleanups and sensitive areas. "
            "They are not a replacement for brushing.\n\n"
            "## Make it positive\n\n"
            "Offer treats and keep sessions short. "
            "Positive routines build long-term comfort.\n\n"
            "A simple tool kit covers most grooming needs for Maine Coons. "
            "Consistency keeps the coat healthy year-round."
        ),
        "meta_title": "Maine Coon Grooming Tools | Frostline Coons",
        "meta_description": "Essential grooming tools for Maine Coons and how to use them safely.",
        "keywords": "Maine Coon grooming tools, slicker brush, long hair cat grooming",
        "cover_image": "https://images.pexels.com/photos/33695311/pexels-photo-33695311.jpeg?cs=srgb&dl=pexels-khang-huy-210723629-33695311.jpg&fm=jpg"
    },
    {
        "title": "Understanding Kitten Body Language: Signals You Can Trust",
        "excerpt": "Learn the calm, everyday signals that show comfort, stress, or curiosity.",
        "content": (
            "Maine Coon kittens communicate with posture, tail position, and slow blinks. "
            "Reading these signals builds trust and prevents stress.\n\n"
            "## Relaxed signals\n\n"
            "Soft eyes, slow blinks, and a gently held tail indicate comfort. "
            "This is a great time for gentle play.\n\n"
            "## Overstimulated signals\n\n"
            "Tail flicks, wide eyes, or sudden stillness can signal stress. "
            "Give space and keep things calm.\n\n"
            "## Curious signals\n\n"
            "Forward ears and a relaxed stance show curiosity. "
            "Encourage exploration without pressure.\n\n"
            "## Respond with patience\n\n"
            "Let your kitten lead interactions and avoid forcing contact. "
            "Patience builds confidence quickly.\n\n"
            "Understanding body language creates a stronger bond. "
            "It helps your kitten feel safe in every interaction."
        ),
        "meta_title": "Kitten Body Language Guide | Frostline Coons",
        "meta_description": "Learn how to read Maine Coon kitten body language and respond with calm confidence.",
        "keywords": "kitten body language, Maine Coon behavior, cat signals",
        "cover_image": "https://source.unsplash.com/1600x900/?cat%20eyes&sig=16"
    },
    {
        "title": "Cat Tree and Climbing Setup for Maine Coons",
        "excerpt": "A climbing setup guide for large, athletic Maine Coon kittens.",
        "content": (
            "Maine Coons thrive with vertical space. "
            "A strong climbing setup builds confidence and prevents boredom.\n\n"
            "## Choose sturdy materials\n\n"
            "Look for wide platforms, thick posts, and stable bases. "
            "Large cats need extra support.\n\n"
            "## Add multiple levels\n\n"
            "Multiple perches let your kitten climb and rest at different heights. "
            "This satisfies natural instincts.\n\n"
            "## Place near natural light\n\n"
            "Window views add enrichment and calm observation time. "
            "A perch by a window is a favorite.\n\n"
            "## Combine with play\n\n"
            "Pair the tree with interactive toys for daily activity. "
            "Short sessions keep energy balanced.\n\n"
            "A good climbing setup is a daily enrichment tool. "
            "It supports a happy, confident Maine Coon."
        ),
        "meta_title": "Cat Tree Setup for Maine Coons | Frostline Coons",
        "meta_description": "How to build a safe, sturdy climbing setup for Maine Coons with cat trees and perches.",
        "keywords": "Maine Coon cat tree, climbing setup, large cat furniture",
        "cover_image": "https://source.unsplash.com/1600x900/?cat%20tree&sig=14"
    },
    {
        "title": "Feeding Transitions: Switching Your Maine Coon Kitten’s Food Safely",
        "excerpt": "A calm, step-by-step approach to changing foods without upsetting digestion.",
        "content": (
            "Food changes should be gradual to protect digestion. "
            "Slow transitions help kittens adjust smoothly.\n\n"
            "## Start with a blend\n\n"
            "Mix small amounts of the new food into the current food. "
            "Increase the new ratio over several days.\n\n"
            "## Watch appetite and stool\n\n"
            "Monitor energy and digestion during the transition. "
            "Slow down if you see signs of sensitivity.\n\n"
            "## Keep portions consistent\n\n"
            "Do not change portion size while switching foods. "
            "Consistency reduces stress on the system.\n\n"
            "## Prioritize hydration\n\n"
            "Fresh water and a bit of wet food can support digestion. "
            "Hydration helps during any diet change.\n\n"
            "A slow, steady transition keeps your kitten comfortable. "
            "Consistency is the safest approach."
        ),
        "meta_title": "Switching Maine Coon Kitten Food | Frostline Coons",
        "meta_description": "How to switch Maine Coon kitten food safely with a gradual, low-stress transition.",
        "keywords": "switch kitten food, Maine Coon nutrition, kitten feeding transition",
        "cover_image": "https://source.unsplash.com/1600x900/?cat%20food&sig=15"
    },
    {
        "title": "Apartment Enrichment for Maine Coons: Small-Space Solutions",
        "excerpt": "Smart enrichment ideas for Maine Coons living in apartments or smaller homes.",
        "content": (
            "Small spaces can still support big, confident cats. "
            "The key is vertical space and daily engagement.\n\n"
            "## Go vertical\n\n"
            "Shelves, perches, and tall trees create climbing space without adding clutter. "
            "Vertical routes make a small space feel large.\n\n"
            "## Add daily play\n\n"
            "Short, consistent play sessions reduce boredom. "
            "Interactive toys are ideal for apartments.\n\n"
            "## Use window views\n\n"
            "Window perches provide stimulation and calm observation time. "
            "This is especially helpful in city apartments.\n\n"
            "## Rotate toys weekly\n\n"
            "New textures and sounds keep interest high. "
            "Rotation prevents boredom.\n\n"
            "Apartment living can be a perfect fit with a thoughtful setup. "
            "Small-space enrichment keeps Maine Coons happy."
        ),
        "meta_title": "Apartment Enrichment for Maine Coons | Frostline Coons",
        "meta_description": "Small-space enrichment ideas for Maine Coons in apartments, including vertical space and play.",
        "keywords": "Maine Coon apartment, cat enrichment small space, apartment cat setup",
        "cover_image": "https://source.unsplash.com/1600x900/?cat%20window&sig=17"
    },
    {
        "title": "Pickup Day Travel Kit: What to Bring When Your Kitten Comes Home",
        "excerpt": "A simple travel kit checklist for pickup day or airport handoff.",
        "content": (
            "A prepared travel kit makes pickup day calmer for everyone. "
            "A few essentials go a long way.\n\n"
            "## Secure carrier\n\n"
            "Bring a sturdy carrier with a soft blanket. "
            "Familiar textures help your kitten relax.\n\n"
            "## Water and wipes\n\n"
            "Bring water and a small bowl for longer trips. "
            "Pet-safe wipes are helpful for quick cleanups.\n\n"
            "## Snacks and comfort items\n\n"
            "A small treat can help during transitions. "
            "Keep the environment quiet and steady.\n\n"
            "## Plan the first hour\n\n"
            "Head straight to the prepared starter room and keep things calm. "
            "A quiet arrival sets the tone.\n\n"
            "A simple travel kit reduces stress and keeps pickup day smooth. "
            "Preparation helps your kitten settle quickly."
        ),
        "meta_title": "Kitten Pickup Day Travel Kit | Frostline Coons",
        "meta_description": "What to bring on pickup day for a Maine Coon kitten, from carriers to comfort items.",
        "keywords": "kitten pickup day, kitten travel kit, Maine Coon delivery prep",
        "cover_image": "https://images.pexels.com/photos/12217163/pexels-photo-12217163.jpeg?cs=srgb&dl=pexels-anna-12217163.jpg&fm=jpg"
    }
]


def normalize_keywords(value):
    if not value:
        return []
    if isinstance(value, (list, tuple)):
        items = value
    else:
        items = []
        for chunk in str(value).replace("\n", ",").split(","):
            if chunk.strip():
                items.append(chunk.strip())
    cleaned = []
    seen = set()
    for item in items:
        key = item.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        cleaned.append(item.strip())
    return cleaned


def merge_keywords(base, extra=None):
    merged = []
    merged.extend(normalize_keywords(base))
    merged.extend(normalize_keywords(extra))
    return ", ".join(normalize_keywords(merged))


def load_seed_posts():
    seed_posts = load_seed_posts()
    return seed_posts


def fetch_settings():
    conn = get_db()
    rows = conn.execute("SELECT key, value FROM site_settings").fetchall()
    conn.close()
    settings = {row["key"]: row["value"] for row in rows}
    for key, value in DEFAULT_SETTINGS.items():
        if not settings.get(key):
            settings[key] = value
    if not settings.get("ga_measurement_id") and app.config.get("GA_MEASUREMENT_ID"):
        settings["ga_measurement_id"] = app.config["GA_MEASUREMENT_ID"]
    if not settings.get("inquiry_email") and app.config.get("SMTP_TO"):
        settings["inquiry_email"] = app.config["SMTP_TO"]
    if not settings.get("reply_to_email") and app.config.get("SMTP_FROM"):
        settings["reply_to_email"] = app.config["SMTP_FROM"]
    return settings


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def add_missing_columns(conn, table, columns):
    existing = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})")}
    for name, ddl in columns.items():
        if name not in existing:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}")


def init_db():
    conn = get_db()

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS kittens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            age INTEGER,
            gender TEXT,
            personality TEXT,
            price REAL DEFAULT 0,
            weight TEXT,
            registration TEXT,
            sire_name TEXT,
            sire_weight TEXT,
            sire_color TEXT,
            sire_image TEXT,
            sire_about TEXT,
            dam_name TEXT,
            dam_weight TEXT,
            dam_color TEXT,
            dam_image TEXT,
            dam_about TEXT,
            video_url TEXT,
            folder TEXT,
            image_count INTEGER DEFAULT 0,
            featured INTEGER DEFAULT 0,
            health_details TEXT,
            color TEXT,
            coat TEXT,
            energy TEXT,
            good_with TEXT,
            bio TEXT,
            highlights TEXT,
            availability TEXT DEFAULT 'Available',
            description TEXT,
            images TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    add_missing_columns(
        conn,
        "kittens",
        {
            "age": "INTEGER",
            "gender": "TEXT",
            "personality": "TEXT",
            "price": "REAL DEFAULT 0",
            "weight": "TEXT",
            "registration": "TEXT",
            "sire_name": "TEXT",
            "sire_weight": "TEXT",
            "sire_color": "TEXT",
            "sire_image": "TEXT",
            "sire_about": "TEXT",
            "dam_name": "TEXT",
            "dam_weight": "TEXT",
            "dam_color": "TEXT",
            "dam_image": "TEXT",
            "dam_about": "TEXT",
            "video_url": "TEXT",
            "folder": "TEXT",
            "image_count": "INTEGER DEFAULT 0",
            "featured": "INTEGER DEFAULT 0",
            "health_details": "TEXT",
            "color": "TEXT",
            "coat": "TEXT",
            "energy": "TEXT",
            "good_with": "TEXT",
            "bio": "TEXT",
            "highlights": "TEXT",
            "availability": "TEXT DEFAULT 'Available'",
            "description": "TEXT",
            "images": "TEXT"
        },
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS testimonials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            author TEXT,
            quote TEXT,
            image TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS site_sections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            section_key TEXT UNIQUE,
            title TEXT,
            body TEXT,
            image TEXT
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS pages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT UNIQUE,
            title TEXT,
            meta_title TEXT,
            meta_description TEXT,
            hero_title TEXT,
            hero_body TEXT,
            hero_image TEXT,
            steps_json TEXT,
            blocks_json TEXT,
            cta_title TEXT,
            cta_body TEXT,
            cta_label TEXT,
            cta_link TEXT
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS blog_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            slug TEXT UNIQUE,
            excerpt TEXT,
            content TEXT,
            cover_image TEXT,
            meta_title TEXT,
            meta_description TEXT,
            keywords TEXT,
            status TEXT DEFAULT 'published',
            published_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS site_settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS inquiries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kitten_id INTEGER,
            name TEXT,
            email TEXT,
            message TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'open',
            inquiry_type TEXT,
            phone TEXT,
            delivery_type TEXT,
            address TEXT,
            payment_method TEXT
        )
        """
    )

    add_missing_columns(
        conn,
        "inquiries",
        {
            "status": "TEXT DEFAULT 'open'",
            "inquiry_type": "TEXT",
            "phone": "TEXT",
            "delivery_type": "TEXT",
            "address": "TEXT",
            "payment_method": "TEXT",
            "deposit_amount": "REAL",
            "balance_due": "REAL",
        },
    )

    seed_defaults(conn)
    conn.commit()
    conn.close()


def seed_defaults(conn):
    kitten_rows = conn.execute("SELECT * FROM kittens").fetchall()
    existing_by_name = {row["name"]: row for row in kitten_rows}

    for kitten in DEFAULT_KITTENS:
        row = existing_by_name.get(kitten["name"])
        payload = {
            "name": kitten["name"],
            "age": kitten["age"],
            "gender": kitten["gender"],
            "personality": kitten["personality"],
            "price": kitten["price"],
            "weight": kitten.get("weight", ""),
            "registration": kitten.get("registration", ""),
            "sire_name": kitten.get("sire_name", ""),
            "sire_weight": kitten.get("sire_weight", ""),
            "sire_color": kitten.get("sire_color", ""),
            "sire_image": kitten.get("sire_image", ""),
            "dam_name": kitten.get("dam_name", ""),
            "dam_weight": kitten.get("dam_weight", ""),
            "dam_color": kitten.get("dam_color", ""),
            "dam_image": kitten.get("dam_image", ""),
            "folder": kitten["folder"],
            "image_count": kitten["image_count"],
            "featured": 1 if kitten["featured"] else 0,
            "health_details": kitten["health_details"],
            "color": kitten["color"],
            "coat": kitten["coat"],
            "energy": kitten["energy"],
            "good_with": json.dumps(kitten["good_with"]),
            "bio": kitten["bio"],
            "highlights": json.dumps(kitten["highlights"]),
            "availability": "Available"
        }

        if row:
            updates = {}
            for key, value in payload.items():
                if key not in row.keys():
                    updates[key] = value
                else:
                    current = row[key]
                    if current is None or current == "":
                        updates[key] = value
            if updates:
                set_clause = ", ".join([f"{k}=?" for k in updates.keys()])
                conn.execute(
                    f"UPDATE kittens SET {set_clause} WHERE id=?",
                    (*updates.values(), row["id"]),
                )
        else:
            columns = ", ".join(payload.keys())
            placeholders = ", ".join(["?"] * len(payload))
            conn.execute(
                f"INSERT INTO kittens ({columns}) VALUES ({placeholders})",
                tuple(payload.values()),
            )

    testimonial_count = conn.execute("SELECT COUNT(*) FROM testimonials").fetchone()[0]
    if testimonial_count == 0:
        for item in DEFAULT_TESTIMONIALS:
            conn.execute(
                "INSERT INTO testimonials (author, quote, image) VALUES (?, ?, ?)",
                (item["author"], item["quote"], item["image"]),
            )

    existing_sections = {
        row["section_key"]: row
        for row in conn.execute("SELECT * FROM site_sections").fetchall()
    }
    for section in DEFAULT_SECTIONS:
        row = existing_sections.get(section["key"])
        if row:
            updates = {}
            if not row["title"]:
                updates["title"] = section["title"]
            if not row["body"]:
                updates["body"] = section["body"]
            if not row["image"]:
                updates["image"] = section["image"]
            if updates:
                set_clause = ", ".join([f"{k}=?" for k in updates.keys()])
                conn.execute(
                    f"UPDATE site_sections SET {set_clause} WHERE section_key=?",
                    (*updates.values(), section["key"]),
                )
        else:
            conn.execute(
                """
                INSERT INTO site_sections (section_key, title, body, image)
                VALUES (?, ?, ?, ?)
                """,
                (section["key"], section["title"], section["body"], section["image"]),
            )

    existing_pages = {
        row["slug"]: row for row in conn.execute("SELECT * FROM pages").fetchall()
    }
    for page in DEFAULT_PAGES:
        row = existing_pages.get(page["slug"])
        payload = {
            "title": page["title"],
            "meta_title": page["meta_title"],
            "meta_description": page["meta_description"],
            "hero_title": page["hero_title"],
            "hero_body": page["hero_body"],
            "hero_image": page["hero_image"],
            "steps_json": json.dumps(page["steps"]),
            "blocks_json": json.dumps(page["blocks"]),
            "cta_title": page["cta_title"],
            "cta_body": page["cta_body"],
            "cta_label": page["cta_label"],
            "cta_link": page["cta_link"],
        }
        if row:
            updates = {}
            for key, value in payload.items():
                if not row[key]:
                    updates[key] = value
            if updates:
                set_clause = ", ".join([f"{k}=?" for k in updates.keys()])
                conn.execute(
                    f"UPDATE pages SET {set_clause} WHERE slug=?",
                    (*updates.values(), page["slug"]),
                )
        else:
            columns = ", ".join(["slug"] + list(payload.keys()))
            placeholders = ", ".join(["?"] * (len(payload) + 1))
            conn.execute(
                f"INSERT INTO pages ({columns}) VALUES ({placeholders})",
                (page["slug"], *payload.values()),
            )

    seed_posts = DEFAULT_BLOG_POSTS
    seed_path = os.path.join(app.root_path, "data", "blog_posts.json")
    if os.path.isfile(seed_path):
        try:
            with open(seed_path, "r", encoding="utf-8") as handle:
                seed_posts = json.load(handle)
        except json.JSONDecodeError:
            seed_posts = DEFAULT_BLOG_POSTS
    seed_posts = list(seed_posts or [])
    random.Random(42).shuffle(seed_posts)

    existing_rows = {
        row["slug"]: row
        for row in conn.execute("SELECT slug, title FROM blog_posts").fetchall()
    }
    existing_titles = {
        (row["title"] or "").strip().lower()
        for row in existing_rows.values()
        if row.get("title")
    }
    max_posts = 50
    current_count = len(existing_rows)
    for post in seed_posts:
        if current_count >= max_posts:
            break
        payload = dict(post)
        base_slug = slugify(payload["title"])
        if base_slug in existing_rows or payload["title"].strip().lower() in existing_titles:
            continue
        slug = ensure_unique_slug(conn, base_slug)
        published_at = payload.get("published_at")

        if published_at:
            conn.execute(
                """
                INSERT INTO blog_posts
                (title, slug, excerpt, content, cover_image, meta_title, meta_description, keywords, status, published_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'published', ?)
                """,
                (
                    payload["title"],
                    slug,
                    payload["excerpt"],
                    payload["content"],
                    payload["cover_image"],
                    payload["meta_title"],
                    payload["meta_description"],
                    payload["keywords"],
                    published_at,
                ),
            )
        else:
            conn.execute(
                """
                INSERT INTO blog_posts
                (title, slug, excerpt, content, cover_image, meta_title, meta_description, keywords, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'published')
                """,
                (
                    payload["title"],
                    slug,
                    payload["excerpt"],
                    payload["content"],
                    payload["cover_image"],
                    payload["meta_title"],
                    payload["meta_description"],
                    payload["keywords"],
                ),
            )
        current_count += 1

    existing_settings = {
        row["key"]: row["value"]
        for row in conn.execute("SELECT key, value FROM site_settings").fetchall()
    }
    for key, value in DEFAULT_SETTINGS.items():
        if not existing_settings.get(key):
            conn.execute(
                "INSERT OR REPLACE INTO site_settings (key, value) VALUES (?, ?)",
                (key, value),
            )


def decode_list(value):
    if not value:
        return []
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return [item.strip() for item in value.split(",") if item.strip()]


def parse_list_text(value):
    if not value:
        return []
    if "\n" in value:
        return [line.strip() for line in value.splitlines() if line.strip()]
    return [item.strip() for item in value.split(",") if item.strip()]


def is_external_url(value):
    return value.startswith("http://") or value.startswith("https://")


def media_url(path):
    if not path:
        return ""
    if is_external_url(path):
        return path
    if path.startswith("/uploads/"):
        return path
    if path.startswith("/static/"):
        return path
    if path.startswith("uploads/"):
        return url_for("uploaded_file", filename=path[len("uploads/"):])
    return url_for("static", filename=path)


def kitten_folder_paths(folder):
    upload_root = os.path.join(app.config["UPLOADS_PATH"], "kittens")
    upload_path = os.path.join(upload_root, folder)
    static_path = os.path.join(app.root_path, "static", "images", folder)
    if os.path.isdir(upload_path):
        return upload_path, True
    if os.path.isdir(static_path):
        return static_path, False
    return upload_path, True


def kitten_image_url(folder, filename):
    if not folder:
        return url_for("static", filename="images/hero_kitten.jpg")
    folder_path, uses_uploads = kitten_folder_paths(folder)
    if uses_uploads:
        return url_for(
            "uploaded_file", filename=f"kittens/{folder}/{filename}"
        )
    return url_for("static", filename=f"images/{folder}/{filename}")


@app.context_processor
def inject_media_helpers():
    sections = fetch_sections()
    settings = fetch_settings()
    service_areas = parse_list_text(settings.get("service_areas"))
    social_links = [
        link
        for link in [
            settings.get("social_facebook"),
            settings.get("social_instagram"),
            settings.get("social_twitter"),
        ]
        if link
    ]
    return {
        "media_url": media_url,
        "kitten_image_url": kitten_image_url,
        "site_sections": sections,
        "site_settings": settings,
        "service_areas": service_areas,
        "social_links": social_links,
        "current_year": datetime.now().year,
    }


def kitten_row_to_dict(row):
    kitten = dict(row)
    kitten["age"] = int(kitten.get("age") or 0)
    kitten["price"] = float(kitten.get("price") or 0)
    kitten["weight"] = kitten.get("weight") or ""
    kitten["registration"] = kitten.get("registration") or ""
    kitten["sire_name"] = kitten.get("sire_name") or ""
    kitten["sire_weight"] = kitten.get("sire_weight") or ""
    kitten["sire_color"] = kitten.get("sire_color") or ""
    kitten["sire_image"] = kitten.get("sire_image") or ""
    kitten["sire_about"] = kitten.get("sire_about") or ""
    kitten["dam_name"] = kitten.get("dam_name") or ""
    kitten["dam_weight"] = kitten.get("dam_weight") or ""
    kitten["dam_color"] = kitten.get("dam_color") or ""
    kitten["dam_image"] = kitten.get("dam_image") or ""
    kitten["dam_about"] = kitten.get("dam_about") or ""
    kitten["video_url"] = kitten.get("video_url") or ""
    kitten["image_count"] = int(kitten.get("image_count") or 0)
    kitten["featured"] = bool(kitten.get("featured"))
    availability = kitten.get("availability") or "Available"
    kitten["availability"] = availability.title()
    kitten["good_with"] = decode_list(kitten.get("good_with"))
    kitten["highlights"] = decode_list(kitten.get("highlights"))
    kitten["bio"] = kitten.get("bio") or kitten.get("description") or ""
    kitten["health_details"] = kitten.get("health_details") or ""
    kitten["personality"] = kitten.get("personality") or ""
    kitten["coat"] = kitten.get("coat") or ""
    kitten["energy"] = kitten.get("energy") or ""
    kitten["color"] = kitten.get("color") or ""
    kitten["folder"] = kitten.get("folder") or ""

    local_images = list_kitten_images(kitten["folder"])
    extra_images = [item.strip() for item in decode_list(kitten.get("images")) if item.strip()]
    kitten["image_urls"] = extra_images

    if local_images:
        kitten["images"] = local_images
        kitten["image_count"] = len(local_images)
        kitten["main_image"] = "1.jpg" if "1.jpg" in local_images else local_images[0]
    else:
        kitten["images"] = []
        kitten["main_image"] = "1.jpg"

    default_image = url_for("static", filename="images/hero_kitten.jpg")
    if local_images:
        main_image_url = kitten_image_url(kitten["folder"], kitten["main_image"])
    elif extra_images:
        main_image_url = media_url(extra_images[0])
    else:
        main_image_url = default_image

    gallery = [
        {"type": "image", "src": kitten_image_url(kitten["folder"], img)}
        for img in local_images
    ]
    gallery += [{"type": "image", "src": media_url(img)} for img in extra_images]

    video_src = media_url(kitten["video_url"]) if kitten["video_url"] else ""
    if video_src:
        gallery.append({"type": "video", "src": video_src})

    main_media_type = "image"
    main_media_src = main_image_url
    if not local_images and not extra_images and video_src:
        main_media_type = "video"
        main_media_src = video_src

    kitten["gallery"] = gallery
    kitten["main_media_type"] = main_media_type
    kitten["main_media_src"] = main_media_src
    kitten["card_image_url"] = main_image_url if main_image_url else default_image
    kitten["video_src"] = video_src
    return kitten


def fetch_kittens(featured_only=False):
    conn = get_db()
    query = "SELECT * FROM kittens"
    params = ()
    if featured_only:
        query += " WHERE featured = 1"
    query += " ORDER BY created_at DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [kitten_row_to_dict(row) for row in rows]


def fetch_kitten(kitten_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM kittens WHERE id = ?", (kitten_id,)).fetchone()
    conn.close()
    return kitten_row_to_dict(row) if row else None


def fetch_testimonials():
    conn = get_db()
    rows = conn.execute("SELECT * FROM testimonials ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(row) for row in rows]


def fetch_sections():
    conn = get_db()
    rows = conn.execute("SELECT * FROM site_sections").fetchall()
    conn.close()
    return {row["section_key"]: dict(row) for row in rows}


def safe_json_load(value, default):
    if not value:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default




def fetch_page(slug):
    conn = get_db()
    row = conn.execute("SELECT * FROM pages WHERE slug = ?", (slug,)).fetchone()
    conn.close()
    if not row:
        return None
    page = dict(row)
    default = next((item for item in DEFAULT_PAGES if item["slug"] == slug), None)
    page["steps"] = safe_json_load(page.get("steps_json"), default["steps"] if default else [])
    page["blocks"] = safe_json_load(page.get("blocks_json"), default["blocks"] if default else [])
    return page


def fetch_blog_posts(published_only=True):
    conn = get_db()
    if published_only:
        rows = conn.execute(
            "SELECT * FROM blog_posts WHERE status = 'published' ORDER BY published_at DESC"
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM blog_posts ORDER BY published_at DESC"
        ).fetchall()
    conn.close()
    posts = []
    for row in rows:
        post = dict(row)
        if not post.get("excerpt") and post.get("content"):
            post["excerpt"] = post["content"][:160].rsplit(" ", 1)[0] + "..."
        posts.append(post)
    return posts


def fetch_blog_post_by_slug(slug):
    conn = get_db()
    row = conn.execute("SELECT * FROM blog_posts WHERE slug = ?", (slug,)).fetchone()
    conn.close()
    if not row:
        return None
    post = dict(row)
    if not post.get("excerpt") and post.get("content"):
        post["excerpt"] = post["content"][:160].rsplit(" ", 1)[0] + "..."
    return post


def ensure_unique_slug(conn, base_slug, post_id=None):
    slug = base_slug
    counter = 1
    while True:
        params = (slug,)
        query = "SELECT id FROM blog_posts WHERE slug = ?"
        row = conn.execute(query, params).fetchone()
        if not row or (post_id and row["id"] == post_id):
            return slug
        counter += 1
        slug = f"{base_slug}-{counter}"


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


def save_uploaded_files(files, folder_path, allowed_exts):
    saved_files = []
    os.makedirs(folder_path, exist_ok=True)
    for index, file in enumerate(files, start=1):
        filename = secure_filename(file.filename)
        if not filename:
            continue
        ext = os.path.splitext(filename)[1].lower()
        if ext not in allowed_exts:
            raise ValueError("Unsupported file type. Please upload JPG images.")
        if ext in {".jpg", ".jpeg"}:
            destination = os.path.join(folder_path, f"{index}.jpg")
        else:
            destination = os.path.join(folder_path, f"{index}{ext}")
        file.save(destination)
        saved_files.append(destination)
    return saved_files


def slugify(value):
    safe = []
    for char in value.lower():
        if char.isalnum():
            safe.append(char)
        else:
            if not safe or safe[-1] != "-":
                safe.append("-")
    return "".join(safe).strip("-")


def list_kitten_images(folder):
    if not folder:
        return []
    folder_path, _ = kitten_folder_paths(folder)
    if not os.path.isdir(folder_path):
        return []
    files = [
        f
        for f in os.listdir(folder_path)
        if os.path.splitext(f)[1].lower() in ALLOWED_KITTEN_IMAGE_EXTS
    ]

    def sort_key(name):
        stem = os.path.splitext(name)[0]
        if stem.isdigit():
            return (0, int(stem))
        return (1, name.lower())

    return sorted(files, key=sort_key)


def set_main_image(folder, filename):
    if not folder or not filename:
        return
    folder_path, _ = kitten_folder_paths(folder)
    target = os.path.join(folder_path, filename)
    main = os.path.join(folder_path, "1.jpg")
    if not os.path.exists(target):
        return
    if os.path.abspath(target) == os.path.abspath(main):
        return

    temp = os.path.join(folder_path, "__temp_main.jpg")
    if os.path.exists(main):
        os.replace(main, temp)
        os.replace(target, main)
        os.replace(temp, target)
    else:
        os.replace(target, main)


def save_kitten(kitten_id=None):
    name = request.form.get("name", "").strip()
    if not name:
        flash("Name is required.", "error")
        return redirect(request.url)

    existing = fetch_kitten(kitten_id) if kitten_id else None

    folder = request.form.get("folder", "").strip() or (existing["folder"] if existing else "")
    folder = secure_filename(folder) if folder else ""
    if not folder:
        folder = slugify(name) or "kitten"

    sire_image = request.form.get("sire_image", "").strip() or (existing.get("sire_image") if existing else "")
    dam_image = request.form.get("dam_image", "").strip() or (existing.get("dam_image") if existing else "")

    video_url = request.form.get("video_url", "").strip() or (existing.get("video_url") if existing else "")
    remove_video = request.form.get("remove_video") == "on"

    image_urls = [item.strip() for item in parse_list_text(request.form.get("image_urls", "")) if item.strip()]

    for parent_key in ("sire", "dam"):
        upload = request.files.get(f"{parent_key}_image_upload")
        if upload and upload.filename:
            ext = os.path.splitext(upload.filename)[1].lower()
            if ext not in ALLOWED_IMAGE_EXTS:
                flash("Unsupported parent image type.", "error")
                return redirect(request.url)
            folder_path = os.path.join(app.config["UPLOADS_PATH"], "parents")
            os.makedirs(folder_path, exist_ok=True)
            filename = f"{slugify(name)}-{parent_key}{ext}"
            upload.save(os.path.join(folder_path, filename))
            if parent_key == "sire":
                sire_image = f"uploads/parents/{filename}"
            else:
                dam_image = f"uploads/parents/{filename}"

    images = [f for f in request.files.getlist("images") if f and f.filename]
    image_count = int(request.form.get("image_count") or (existing["image_count"] if existing else 0))

    if images:
        try:
            folder_path = os.path.join(app.config["UPLOADS_PATH"], "kittens", folder)
            saved = save_uploaded_files(images, folder_path, ALLOWED_KITTEN_IMAGE_EXTS)
            image_count = len(saved)
        except ValueError as exc:
            flash(str(exc), "error")
            return redirect(request.url)
    elif kitten_id is None and image_count == 0 and not image_urls:
        flash("Please upload at least one JPG image or add an image URL.", "error")
        return redirect(request.url)

    image_files = list_kitten_images(folder)
    if image_files:
        image_count = len(image_files)

    video_upload = request.files.get("video_upload")
    if video_upload and video_upload.filename:
        ext = os.path.splitext(video_upload.filename)[1].lower()
        if ext not in ALLOWED_VIDEO_EXTS:
            flash("Unsupported video type. Please upload MP4, WebM, or MOV.", "error")
            return redirect(request.url)
        folder_path = os.path.join(app.config["UPLOADS_PATH"], "videos")
        os.makedirs(folder_path, exist_ok=True)
        filename = f"{slugify(name) or 'kitten'}-video{ext}"
        video_upload.save(os.path.join(folder_path, filename))
        video_url = f"uploads/videos/{filename}"

    if remove_video and not (video_upload and video_upload.filename):
        video_url = ""

    availability = request.form.get("availability", "").strip().title()
    if availability not in {"Available", "Reserved", "Sold"}:
        availability = "Available"

    payload = {
        "name": name,
        "age": int(request.form.get("age") or 0),
        "gender": request.form.get("gender", "").strip(),
        "personality": request.form.get("personality", "").strip(),
        "price": float(request.form.get("price") or 0),
        "weight": request.form.get("weight", "").strip(),
        "registration": request.form.get("registration", "").strip(),
        "sire_name": request.form.get("sire_name", "").strip(),
        "sire_weight": request.form.get("sire_weight", "").strip(),
        "sire_color": request.form.get("sire_color", "").strip(),
        "sire_image": sire_image,
        "sire_about": request.form.get("sire_about", "").strip(),
        "dam_name": request.form.get("dam_name", "").strip(),
        "dam_weight": request.form.get("dam_weight", "").strip(),
        "dam_color": request.form.get("dam_color", "").strip(),
        "dam_image": dam_image,
        "dam_about": request.form.get("dam_about", "").strip(),
        "video_url": video_url,
        "folder": folder,
        "image_count": image_count,
        "featured": 1 if request.form.get("featured") == "on" else 0,
        "health_details": request.form.get("health_details", "").strip(),
        "color": request.form.get("color", "").strip(),
        "coat": request.form.get("coat", "").strip(),
        "energy": request.form.get("energy", "").strip(),
        "good_with": json.dumps(parse_list_text(request.form.get("good_with", ""))),
        "bio": request.form.get("bio", "").strip(),
        "highlights": json.dumps(parse_list_text(request.form.get("highlights", ""))),
        "availability": availability,
        "images": json.dumps(image_urls)
    }

    conn = get_db()
    if kitten_id:
        set_clause = ", ".join([f"{k}=?" for k in payload.keys()])
        conn.execute(
            f"UPDATE kittens SET {set_clause} WHERE id = ?",
            (*payload.values(), kitten_id),
        )
        conn.commit()
        conn.close()
        flash("Kitten updated.", "success")
    else:
        columns = ", ".join(payload.keys())
        placeholders = ", ".join(["?"] * len(payload))
        conn.execute(
            f"INSERT INTO kittens ({columns}) VALUES ({placeholders})",
            tuple(payload.values()),
        )
        conn.commit()
        conn.close()
        flash("Kitten added.", "success")

    return redirect(url_for("admin_kittens"))


def save_testimonial(testimonial_id=None):
    author = request.form.get("author", "").strip()
    quote = request.form.get("quote", "").strip()
    if not author or not quote:
        flash("Author and quote are required.", "error")
        return redirect(request.url)

    image_path = request.form.get("image", "").strip()
    upload = request.files.get("image_upload")
    if upload and upload.filename:
        ext = os.path.splitext(upload.filename)[1].lower()
        if ext not in ALLOWED_IMAGE_EXTS:
            flash("Unsupported image type.", "error")
            return redirect(request.url)
        folder = os.path.join(app.config["UPLOADS_PATH"], "testimonials")
        os.makedirs(folder, exist_ok=True)
        filename = f"{slugify(author) or 'testimonial'}{ext}"
        upload.save(os.path.join(folder, filename))
        image_path = f"uploads/testimonials/{filename}"

    conn = get_db()
    if testimonial_id:
        conn.execute(
            """
            UPDATE testimonials
            SET author = ?, quote = ?, image = ?
            WHERE id = ?
            """,
            (author, quote, image_path, testimonial_id),
        )
        conn.commit()
        conn.close()
        flash("Testimonial updated.", "success")
    else:
        conn.execute(
            "INSERT INTO testimonials (author, quote, image) VALUES (?, ?, ?)",
            (author, quote, image_path),
        )
        conn.commit()
        conn.close()
        flash("Testimonial added.", "success")

    return redirect(url_for("admin_testimonials"))


def save_blog_post(post_id=None):
    title = request.form.get("title", "").strip()
    if not title:
        flash("Title is required.", "error")
        return redirect(request.url)

    slug_input = request.form.get("slug", "").strip()
    base_slug = slugify(slug_input or title)

    excerpt = request.form.get("excerpt", "").strip()
    content = request.form.get("content", "").strip()
    meta_title = request.form.get("meta_title", "").strip()
    meta_description = request.form.get("meta_description", "").strip()
    keywords = request.form.get("keywords", "").strip()
    status = request.form.get("status", "published").strip() or "published"
    published_at = request.form.get("published_at", "").strip()

    cover_image = request.form.get("cover_image", "").strip()
    upload = request.files.get("cover_upload")
    if upload and upload.filename:
        ext = os.path.splitext(upload.filename)[1].lower()
        if ext not in ALLOWED_IMAGE_EXTS:
            flash("Unsupported image type.", "error")
            return redirect(request.url)
        folder = os.path.join(app.config["UPLOADS_PATH"], "blog")
        os.makedirs(folder, exist_ok=True)
        filename = f"{base_slug}{ext}"
        upload.save(os.path.join(folder, filename))
        cover_image = f"uploads/blog/{filename}"

    conn = get_db()
    slug = ensure_unique_slug(conn, base_slug, post_id)

    if post_id:
        conn.execute(
            """
            UPDATE blog_posts
            SET title = ?, slug = ?, excerpt = ?, content = ?, cover_image = ?,
                meta_title = ?, meta_description = ?, keywords = ?, status = ?,
                published_at = COALESCE(NULLIF(?, ''), published_at),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                title,
                slug,
                excerpt,
                content,
                cover_image,
                meta_title,
                meta_description,
                keywords,
                status,
                published_at,
                post_id,
            ),
        )
        conn.commit()
        conn.close()
        flash("Blog post updated.", "success")
    else:
        conn.execute(
            """
            INSERT INTO blog_posts
            (title, slug, excerpt, content, cover_image, meta_title, meta_description, keywords, status, published_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, COALESCE(NULLIF(?, ''), CURRENT_TIMESTAMP))
            """,
            (
                title,
                slug,
                excerpt,
                content,
                cover_image,
                meta_title,
                meta_description,
                keywords,
                status,
                published_at,
            ),
        )
        conn.commit()
        conn.close()
        flash("Blog post created.", "success")

    return redirect(url_for("admin_blog"))


def save_delivery_page():
    title = request.form.get("title", "").strip()
    meta_title = request.form.get("meta_title", "").strip()
    meta_description = request.form.get("meta_description", "").strip()
    hero_title = request.form.get("hero_title", "").strip()
    hero_body = request.form.get("hero_body", "").strip()
    hero_image = request.form.get("hero_image", "").strip()

    hero_upload = request.files.get("hero_image_upload")
    if hero_upload and hero_upload.filename:
        ext = os.path.splitext(hero_upload.filename)[1].lower()
        if ext not in ALLOWED_IMAGE_EXTS:
            flash("Unsupported hero image type.", "error")
            return redirect(request.url)
        folder = os.path.join(app.config["UPLOADS_PATH"], "pages")
        os.makedirs(folder, exist_ok=True)
        filename = f"delivery-hero{ext}"
        hero_upload.save(os.path.join(folder, filename))
        hero_image = f"uploads/pages/{filename}"

    steps = []
    for idx in range(1, 4):
        step_title = request.form.get(f"step_title_{idx}", "").strip()
        step_body = request.form.get(f"step_body_{idx}", "").strip()
        if step_title or step_body:
            steps.append({"title": step_title, "body": step_body})

    blocks = []
    for idx in range(1, 5):
        block_title = request.form.get(f"block_title_{idx}", "").strip()
        block_body = request.form.get(f"block_body_{idx}", "").strip()
        block_image = request.form.get(f"block_image_{idx}", "").strip()
        layout = request.form.get(f"block_layout_{idx}", "left").strip() or "left"

        upload = request.files.get(f"block_image_upload_{idx}")
        if upload and upload.filename:
            ext = os.path.splitext(upload.filename)[1].lower()
            if ext not in ALLOWED_IMAGE_EXTS:
                flash("Unsupported block image type.", "error")
                return redirect(request.url)
            folder = os.path.join(app.config["UPLOADS_PATH"], "pages")
            os.makedirs(folder, exist_ok=True)
            filename = f"delivery-block-{idx}{ext}"
            upload.save(os.path.join(folder, filename))
            block_image = f"uploads/pages/{filename}"

        if block_title or block_body or block_image:
            blocks.append(
                {
                    "title": block_title,
                    "body": block_body,
                    "image": block_image,
                    "layout": layout,
                }
            )

    cta_title = request.form.get("cta_title", "").strip()
    cta_body = request.form.get("cta_body", "").strip()
    cta_label = request.form.get("cta_label", "").strip()
    cta_link = request.form.get("cta_link", "").strip()

    conn = get_db()
    conn.execute(
        """
        UPDATE pages
        SET title = ?, meta_title = ?, meta_description = ?, hero_title = ?, hero_body = ?, hero_image = ?,
            steps_json = ?, blocks_json = ?, cta_title = ?, cta_body = ?, cta_label = ?, cta_link = ?
        WHERE slug = 'delivery'
        """,
        (
            title,
            meta_title,
            meta_description,
            hero_title,
            hero_body,
            hero_image,
            json.dumps(steps),
            json.dumps(blocks),
            cta_title,
            cta_body,
            cta_label,
            cta_link,
        ),
    )
    conn.commit()
    conn.close()
    flash("Delivery page updated.", "success")
    return redirect(url_for("admin_delivery_page"))


def save_generic_page(slug):
    title = request.form.get("title", "").strip()
    meta_title = request.form.get("meta_title", "").strip()
    meta_description = request.form.get("meta_description", "").strip()
    hero_title = request.form.get("hero_title", "").strip()
    hero_body = request.form.get("hero_body", "").strip()
    hero_image = request.form.get("hero_image", "").strip()

    hero_upload = request.files.get("hero_image_upload")
    if hero_upload and hero_upload.filename:
        ext = os.path.splitext(hero_upload.filename)[1].lower()
        if ext not in ALLOWED_IMAGE_EXTS:
            flash("Unsupported hero image type.", "error")
            return redirect(request.url)
        folder = os.path.join(app.config["UPLOADS_PATH"], "pages")
        os.makedirs(folder, exist_ok=True)
        filename = f"{slug}-hero{ext}"
        hero_upload.save(os.path.join(folder, filename))
        hero_image = f"uploads/pages/{filename}"

    blocks = []
    for idx in range(1, 5):
        block_title = request.form.get(f"block_title_{idx}", "").strip()
        block_body = request.form.get(f"block_body_{idx}", "").strip()
        block_image = request.form.get(f"block_image_{idx}", "").strip()
        layout = request.form.get(f"block_layout_{idx}", "left").strip() or "left"

        upload = request.files.get(f"block_image_upload_{idx}")
        if upload and upload.filename:
            ext = os.path.splitext(upload.filename)[1].lower()
            if ext not in ALLOWED_IMAGE_EXTS:
                flash("Unsupported block image type.", "error")
                return redirect(request.url)
            folder = os.path.join(app.config["UPLOADS_PATH"], "pages")
            os.makedirs(folder, exist_ok=True)
            filename = f"{slug}-block-{idx}{ext}"
            upload.save(os.path.join(folder, filename))
            block_image = f"uploads/pages/{filename}"

        if block_title or block_body or block_image:
            blocks.append(
                {
                    "title": block_title,
                    "body": block_body,
                    "image": block_image,
                    "layout": layout,
                }
            )

    cta_title = request.form.get("cta_title", "").strip()
    cta_body = request.form.get("cta_body", "").strip()
    cta_label = request.form.get("cta_label", "").strip()
    cta_link = request.form.get("cta_link", "").strip()

    conn = get_db()
    conn.execute(
        """
        UPDATE pages
        SET title = ?, meta_title = ?, meta_description = ?, hero_title = ?, hero_body = ?, hero_image = ?,
            blocks_json = ?, cta_title = ?, cta_body = ?, cta_label = ?, cta_link = ?
        WHERE slug = ?
        """,
        (
            title,
            meta_title,
            meta_description,
            hero_title,
            hero_body,
            hero_image,
            json.dumps(blocks),
            cta_title,
            cta_body,
            cta_label,
            cta_link,
            slug,
        ),
    )
    conn.commit()
    conn.close()
    flash("Page updated.", "success")
    return redirect(url_for("admin_pages"))


def send_inquiry_email(inquiry, kitten):
    if not app.config["SMTP_HOST"]:
        return

    settings = fetch_settings()
    business_name = settings.get("business_name") or "Frostline Coons"
    reply_to = settings.get("reply_to_email") or app.config["SMTP_FROM"]
    to_addr = settings.get("inquiry_email") or app.config["SMTP_TO"]
    from_addr = app.config["SMTP_FROM"]

    subject = f"New {inquiry['inquiry_type'].title()} Inquiry - {kitten.get('name', 'Kitten')}"

    total = f"${kitten.get('price', 0):.0f}"
    deposit = f"${inquiry.get('deposit_amount', 0):.0f}"
    balance = f"${inquiry.get('balance_due', 0):.0f}"
    address = settings.get("business_address") or ""
    phone = settings.get("business_phone") or ""
    footer_bits = " • ".join([item for item in [address, phone, reply_to] if item])
    invoice_html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background:#f6f2ec; padding:24px;">
      <div style="max-width:640px;margin:0 auto;background:#ffffff;border-radius:16px;padding:24px;">
        <h2 style="margin-top:0;color:#2c2a28;">{business_name} — Inquiry Invoice</h2>
        <p style="color:#4a453f;">New {inquiry['inquiry_type']} inquiry received.</p>
        <table style="width:100%;border-collapse:collapse;margin:16px 0;">
          <tr>
            <th align="left" style="padding:8px;border-bottom:1px solid #eee;">Item</th>
            <th align="right" style="padding:8px;border-bottom:1px solid #eee;">Price</th>
          </tr>
          <tr>
            <td style="padding:8px;">{kitten.get('name', 'Kitten')} ({kitten.get('gender', '')})</td>
            <td align="right" style="padding:8px;">{total}</td>
          </tr>
          <tr>
            <td style="padding:8px;">Reservation Amount</td>
            <td align="right" style="padding:8px;">{deposit}</td>
          </tr>
          <tr>
            <td style="padding:8px;">Balance Due</td>
            <td align="right" style="padding:8px;">{balance}</td>
          </tr>
          <tr>
            <td style="padding:8px;font-weight:bold;">Total</td>
            <td align="right" style="padding:8px;font-weight:bold;">{total}</td>
          </tr>
        </table>
        <h3 style="margin-bottom:6px;">Customer Details</h3>
        <p style="margin:0;">Name: {inquiry['name']}</p>
        <p style="margin:0;">Email: {inquiry['email']}</p>
        <p style="margin:0;">Phone: {inquiry.get('phone') or '—'}</p>
        <p style="margin:0;">Delivery: {inquiry.get('delivery_type') or '—'}</p>
        <p style="margin:0;">Address: {inquiry.get('address') or '—'}</p>
        <p style="margin:0;">Payment: {inquiry.get('payment_method') or '—'}</p>
        <p style="margin-top:16px;color:#4a453f;">Message:</p>
        <p style="margin:0;color:#2c2a28;">{inquiry['message'] or '—'}</p>
        {f"<p style='margin-top:16px;font-size:13px;color:#6a6a6a;'>{footer_bits}</p>" if footer_bits else ""}
      </div>
    </body>
    </html>
    """

    invoice_text = (
        f"New {inquiry['inquiry_type']} inquiry\n"
        f"Kitten: {kitten.get('name', 'Kitten')} - {total}\n"
        f"Reservation Amount: {deposit}\n"
        f"Balance Due: {balance}\n"
        f"Name: {inquiry['name']}\n"
        f"Email: {inquiry['email']}\n"
        f"Phone: {inquiry.get('phone') or '-'}\n"
        f"Delivery: {inquiry.get('delivery_type') or '-'}\n"
        f"Address: {inquiry.get('address') or '-'}\n"
        f"Payment: {inquiry.get('payment_method') or '-'}\n"
        f"Message: {inquiry['message'] or '-'}\n"
    )

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = from_addr
    message["To"] = to_addr
    if reply_to:
        message["Reply-To"] = reply_to
    message.set_content(invoice_text)
    message.add_alternative(invoice_html, subtype="html")

    if app.config["SMTP_USE_SSL"]:
        with smtplib.SMTP_SSL(app.config["SMTP_HOST"], app.config["SMTP_PORT"]) as server:
            if app.config["SMTP_USER"]:
                server.login(app.config["SMTP_USER"], app.config["SMTP_PASS"])
            server.send_message(message)
    else:
        with smtplib.SMTP(app.config["SMTP_HOST"], app.config["SMTP_PORT"]) as server:
            if app.config["SMTP_USE_TLS"]:
                server.starttls()
            if app.config["SMTP_USER"]:
                server.login(app.config["SMTP_USER"], app.config["SMTP_PASS"])
            server.send_message(message)


init_db()

# -------------------- ROUTES --------------------
@app.after_request
def add_cache_headers(response):
    if request.path.startswith("/static/") or request.path.startswith("/uploads/"):
        response.headers["Cache-Control"] = "public, max-age=2592000"
    elif request.path in ("/sitemap.xml", "/robots.txt"):
        response.headers["Cache-Control"] = "public, max-age=3600"
    return response


@app.route("/")
def index():
    featured = fetch_kittens(featured_only=True)
    testimonials = fetch_testimonials()
    sections = fetch_sections()
    settings = fetch_settings()
    hero = sections.get("hero") if sections else None
    hero_image = hero.get("image") if hero and hero.get("image") else "images/hero_kitten.jpg"
    return render_template(
        "index.html",
        featured=featured,
        testimonials=testimonials,
        sections=sections,
        meta_title="Frostline Coons | Maine Coon Kittens",
        meta_description=(
            "Ethically raised Maine Coon kittens with loving socialization, "
            "health-focused care, and lifelong support."
        ),
        meta_keywords=merge_keywords(
            settings.get("seo_keywords"),
            "featured Maine Coon kittens, Maine Coon kittens raised with care",
        ),
        meta_image=media_url(hero_image),
    )


@app.route("/available_kittens")
def available_kittens():
    kittens = fetch_kittens()[:12]
    meta_image = kittens[0].get("card_image_url") if kittens else media_url("images/hero_kitten.jpg")
    settings = fetch_settings()
    return render_template(
        "available_kittens.html",
        kittens=kittens,
        meta_title="Available Maine Coon Kittens | Frostline Coons",
        meta_description="View available Maine Coon kittens, pricing, and details. Reserve or inquire today.",
        meta_keywords=merge_keywords(
            settings.get("seo_keywords"),
            "available Maine Coon kittens, reserve Maine Coon kitten, buy Maine Coon kitten",
        ),
        meta_image=meta_image,
    )


@app.route("/kitten/<int:kitten_id>")
def kitten_details(kitten_id):
    kitten = fetch_kitten(kitten_id)
    if not kitten:
        abort(404)
    sections = fetch_sections()
    settings = fetch_settings()
    meta_image = kitten.get("card_image_url") or media_url("images/hero_kitten.jpg")
    return render_template(
        "kitten_details.html",
        kitten=kitten,
        sections=sections,
        reservation_deposit=app.config["RESERVATION_DEPOSIT"],
        meta_title=f"{kitten.get('name', 'Kitten')} | Frostline Coons",
        meta_description=kitten.get("description")
        or kitten.get("bio")
        or "Meet this Maine Coon kitten and learn about personality, care, and availability.",
        meta_keywords=merge_keywords(
            settings.get("seo_keywords"),
            [
                kitten.get("name", "Maine Coon kitten"),
                f"{kitten.get('name', 'Maine Coon kitten')} for sale",
                "Maine Coon kitten details",
            ],
        ),
        meta_image=meta_image,
    )


@app.route("/inquiry", methods=["POST"])
def submit_inquiry():
    kitten_id = request.form.get("kitten_id")
    inquiry_type = request.form.get("inquiry_type", "reserve").strip().lower()
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()
    message = request.form.get("message", "").strip()
    delivery_type = request.form.get("delivery_type", "").strip()
    address = request.form.get("address", "").strip()
    payment_method = request.form.get("payment_method", "").strip()

    if not kitten_id or not name or not email:
        return {"ok": False, "error": "Missing required fields."}, 400

    kitten = fetch_kitten(int(kitten_id))
    if not kitten:
        return {"ok": False, "error": "Kitten not found."}, 404
    if (kitten.get("availability") or "").lower() != "available":
        return {"ok": False, "error": "This kitten is no longer available."}, 400

    price = float(kitten.get("price") or 0)
    if inquiry_type == "reserve":
        deposit_amount = min(price, app.config["RESERVATION_DEPOSIT"])
        balance_due = max(0, price - deposit_amount)
    else:
        deposit_amount = 0
        balance_due = price

    conn = get_db()
    conn.execute(
        """
        INSERT INTO inquiries
        (kitten_id, name, email, message, status, inquiry_type, phone, delivery_type, address, payment_method, deposit_amount, balance_due)
        VALUES (?, ?, ?, ?, 'open', ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            kitten_id,
            name,
            email,
            message,
            inquiry_type,
            phone,
            delivery_type,
            address,
            payment_method,
            deposit_amount,
            balance_due,
        ),
    )
    conn.commit()
    conn.close()

    try:
        send_inquiry_email(
            {
                "name": name,
                "email": email,
                "phone": phone,
                "message": message,
                "inquiry_type": inquiry_type,
                "delivery_type": delivery_type,
                "address": address,
                "payment_method": payment_method,
                "deposit_amount": deposit_amount,
                "balance_due": balance_due,
            },
            kitten,
        )
    except Exception as exc:
        return {"ok": False, "error": f"Email failed: {exc}"}, 500

    return {"ok": True}


@app.route("/delivery")
def delivery():
    page = fetch_page("delivery")
    if not page:
        abort(404)
    settings = fetch_settings()
    return render_template(
        "delivery.html",
        page=page,
        meta_title=page.get("meta_title") or page.get("title") or "Delivery & Arrival",
        meta_description=page.get("meta_description") or page.get("hero_body"),
        meta_keywords=merge_keywords(
            settings.get("seo_keywords"),
            "Maine Coon kitten delivery, kitten transport, airport pickup",
        ),
        meta_image=media_url(page.get("hero_image") or "images/hero_delivery.jpg"),
    )


def render_generic_page(slug):
    page = fetch_page(slug)
    if not page:
        abort(404)
    settings = fetch_settings()
    return render_template(
        "page.html",
        page=page,
        meta_title=page.get("meta_title") or page.get("title"),
        meta_description=page.get("meta_description") or page.get("hero_body"),
        meta_keywords=merge_keywords(
            settings.get("seo_keywords"),
            page.get("meta_title") or page.get("title"),
        ),
        meta_image=media_url(page.get("hero_image") or "images/hero_kitten.jpg"),
    )


@app.route("/about")
def about():
    return render_generic_page("about")


@app.route("/faqs")
def faqs():
    return render_generic_page("faqs")


@app.route("/contact")
def contact():
    return render_generic_page("contact")


@app.route("/blog")
def blog_index():
    posts = fetch_blog_posts()
    settings = fetch_settings()
    return render_template(
        "blog/index.html",
        posts=posts,
        meta_title="Maine Coon Blog | Frostline Coons",
        meta_description="Maine Coon care guides, breed insights, and kitten tips from Frostline Coons.",
        meta_keywords=merge_keywords(
            settings.get("seo_keywords"),
            "Maine Coon blog, Maine Coon care guides, kitten tips",
        ),
        meta_image=media_url("images/hero_kitten.jpg"),
    )


@app.route("/blog/<slug>")
def blog_post(slug):
    post = fetch_blog_post_by_slug(slug)
    if not post or post.get("status") != "published":
        abort(404)
    settings = fetch_settings()
    cover = post.get("cover_image") or "images/hero_kitten.jpg"
    return render_template(
        "blog/post.html",
        post=post,
        meta_title=post.get("meta_title") or post.get("title") or "Maine Coon Blog",
        meta_description=post.get("meta_description") or post.get("excerpt"),
        meta_keywords=merge_keywords(settings.get("seo_keywords"), post.get("keywords")),
        meta_image=media_url(cover),
        og_type="article",
    )


@app.route("/sitemap.xml")
def sitemap():
    base_url = request.url_root.rstrip("/")
    urls = [
        f"{base_url}{url_for('index')}",
        f"{base_url}{url_for('available_kittens')}",
        f"{base_url}{url_for('delivery')}",
        f"{base_url}{url_for('about')}",
        f"{base_url}{url_for('faqs')}",
        f"{base_url}{url_for('contact')}",
        f"{base_url}{url_for('blog_index')}",
    ]

    for kitten in fetch_kittens():
        urls.append(f"{base_url}{url_for('kitten_details', kitten_id=kitten['id'])}")

    for post in fetch_blog_posts():
        urls.append(f"{base_url}{url_for('blog_post', slug=post['slug'])}")

    xml_items = "\n".join([f"  <url><loc>{loc}</loc></url>" for loc in urls])
    xml = (
        "<?xml version='1.0' encoding='UTF-8'?>\n"
        "<urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'>\n"
        f"{xml_items}\n"
        "</urlset>"
    )
    return Response(xml, mimetype="application/xml")


@app.route("/robots.txt")
def robots():
    base_url = request.url_root.rstrip("/")
    content = "User-agent: *\nAllow: /\nSitemap: " + f"{base_url}/sitemap.xml\n"
    return Response(content, mimetype="text/plain")


@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOADS_PATH"], filename)


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        if (
            username == app.config["ADMIN_USERNAME"]
            and password == app.config["ADMIN_PASSWORD"]
        ):
            session["admin_logged_in"] = True
            return redirect(request.args.get("next") or url_for("admin_dashboard"))
        flash("Invalid credentials. Please try again.", "error")
    return render_template("admin/login.html")


@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))


@app.route("/admin")
@login_required
def admin_dashboard():
    conn = get_db()
    kitten_count = conn.execute("SELECT COUNT(*) FROM kittens").fetchone()[0]
    testimonial_count = conn.execute("SELECT COUNT(*) FROM testimonials").fetchone()[0]
    inquiry_count = conn.execute("SELECT COUNT(*) FROM inquiries").fetchone()[0]
    recent_inquiries = conn.execute(
        "SELECT * FROM inquiries ORDER BY created_at DESC LIMIT 5"
    ).fetchall()
    conn.close()
    return render_template(
        "admin/dashboard.html",
        kitten_count=kitten_count,
        testimonial_count=testimonial_count,
        inquiry_count=inquiry_count,
        recent_inquiries=recent_inquiries,
    )


@app.route("/admin/kittens")
@login_required
def admin_kittens():
    kittens = fetch_kittens()
    return render_template("admin/kittens_list.html", kittens=kittens)


@app.route("/admin/kittens/new", methods=["GET", "POST"])
@login_required
def admin_kittens_new():
    if request.method == "POST":
        return save_kitten()
    return render_template(
        "admin/kitten_form.html", kitten=None, mode="new", kitten_images=[]
    )


@app.route("/admin/kittens/<int:kitten_id>/edit", methods=["GET", "POST"])
@login_required
def admin_kittens_edit(kitten_id):
    kitten = fetch_kitten(kitten_id)
    if not kitten:
        abort(404)
    kitten_images = list_kitten_images(kitten.get("folder"))
    if request.method == "POST":
        return save_kitten(kitten_id)
    return render_template(
        "admin/kitten_form.html",
        kitten=kitten,
        mode="edit",
        kitten_images=kitten_images,
    )


@app.route("/admin/kittens/<int:kitten_id>/delete", methods=["POST"])
@login_required
def admin_kittens_delete(kitten_id):
    conn = get_db()
    conn.execute("DELETE FROM kittens WHERE id = ?", (kitten_id,))
    conn.commit()
    conn.close()
    flash("Kitten deleted.", "success")
    return redirect(url_for("admin_kittens"))


@app.route("/admin/kittens/<int:kitten_id>/images/main", methods=["POST"])
@login_required
def admin_kittens_set_main_image(kitten_id):
    kitten = fetch_kitten(kitten_id)
    if not kitten:
        abort(404)
    filename = os.path.basename(request.form.get("filename", "").strip())
    images = list_kitten_images(kitten.get("folder"))
    if filename not in images:
        flash("Image not found.", "error")
        return redirect(url_for("admin_kittens_edit", kitten_id=kitten_id))

    set_main_image(kitten.get("folder"), filename)
    flash("Main image updated.", "success")
    return redirect(url_for("admin_kittens_edit", kitten_id=kitten_id))


@app.route("/admin/kittens/<int:kitten_id>/images/delete", methods=["POST"])
@login_required
def admin_kittens_delete_image(kitten_id):
    kitten = fetch_kitten(kitten_id)
    if not kitten:
        abort(404)
    filename = os.path.basename(request.form.get("filename", "").strip())
    folder = kitten.get("folder")
    images = list_kitten_images(folder)
    if filename not in images:
        flash("Image not found.", "error")
        return redirect(url_for("admin_kittens_edit", kitten_id=kitten_id))
    if len(images) <= 1:
        flash("At least one image is required.", "error")
        return redirect(url_for("admin_kittens_edit", kitten_id=kitten_id))

    folder_path, _ = kitten_folder_paths(folder)
    path = os.path.join(folder_path, filename)
    try:
        os.remove(path)
    except FileNotFoundError:
        flash("Image not found on disk.", "error")
        return redirect(url_for("admin_kittens_edit", kitten_id=kitten_id))

    images_after = list_kitten_images(folder)
    if "1.jpg" not in images_after and images_after:
        set_main_image(folder, images_after[0])

    conn = get_db()
    conn.execute(
        "UPDATE kittens SET image_count = ? WHERE id = ?",
        (len(images_after), kitten_id),
    )
    conn.commit()
    conn.close()
    flash("Image removed.", "success")
    return redirect(url_for("admin_kittens_edit", kitten_id=kitten_id))


@app.route("/admin/testimonials")
@login_required
def admin_testimonials():
    testimonials = fetch_testimonials()
    return render_template("admin/testimonials_list.html", testimonials=testimonials)


@app.route("/admin/testimonials/new", methods=["GET", "POST"])
@login_required
def admin_testimonials_new():
    if request.method == "POST":
        return save_testimonial()
    return render_template("admin/testimonial_form.html", testimonial=None, mode="new")


@app.route("/admin/testimonials/<int:testimonial_id>/edit", methods=["GET", "POST"])
@login_required
def admin_testimonials_edit(testimonial_id):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM testimonials WHERE id = ?", (testimonial_id,)
    ).fetchone()
    conn.close()
    if not row:
        abort(404)
    testimonial = dict(row)
    if request.method == "POST":
        return save_testimonial(testimonial_id)
    return render_template(
        "admin/testimonial_form.html", testimonial=testimonial, mode="edit"
    )


@app.route("/admin/testimonials/<int:testimonial_id>/delete", methods=["POST"])
@login_required
def admin_testimonials_delete(testimonial_id):
    conn = get_db()
    conn.execute("DELETE FROM testimonials WHERE id = ?", (testimonial_id,))
    conn.commit()
    conn.close()
    flash("Testimonial deleted.", "success")
    return redirect(url_for("admin_testimonials"))


@app.route("/admin/sections", methods=["GET", "POST"])
@login_required
def admin_sections():
    conn = get_db()
    if request.method == "POST":
        for section in DEFAULT_SECTIONS:
            key = section["key"]
            title = request.form.get(f"{key}_title", "").strip()
            body = request.form.get(f"{key}_body", "").strip()
            image = request.form.get(f"{key}_image", "").strip()

            upload = request.files.get(f"{key}_image_upload")
            if upload and upload.filename:
                ext = os.path.splitext(upload.filename)[1].lower()
                if ext not in ALLOWED_IMAGE_EXTS:
                    flash("Unsupported image type for sections.", "error")
                    return redirect(url_for("admin_sections"))
                folder = os.path.join(app.config["UPLOADS_PATH"], "sections")
                os.makedirs(folder, exist_ok=True)
                filename = f"{key}{ext}"
                upload.save(os.path.join(folder, filename))
                image = f"uploads/sections/{filename}"

            conn.execute(
                """
                UPDATE site_sections
                SET title = ?, body = ?, image = ?
                WHERE section_key = ?
                """,
                (title, body, image, key),
            )

        conn.commit()
        conn.close()
        flash("Sections updated.", "success")
        return redirect(url_for("admin_sections"))

    rows = conn.execute("SELECT * FROM site_sections").fetchall()
    conn.close()
    sections = {row["section_key"]: dict(row) for row in rows}
    ordered = [sections[key["key"]] for key in DEFAULT_SECTIONS if key["key"] in sections]
    return render_template("admin/sections.html", sections=ordered)


@app.route("/admin/settings", methods=["GET", "POST"])
@login_required
def admin_settings():
    settings = fetch_settings()
    if request.method == "POST":
        updates = {
            "business_name": request.form.get("business_name", "").strip(),
            "reply_to_email": request.form.get("reply_to_email", "").strip(),
            "inquiry_email": request.form.get("inquiry_email", "").strip(),
            "business_address": request.form.get("business_address", "").strip(),
            "business_phone": request.form.get("business_phone", "").strip(),
            "seo_keywords": request.form.get("seo_keywords", "").strip(),
            "service_areas": request.form.get("service_areas", "").strip(),
            "ga_measurement_id": request.form.get("ga_measurement_id", "").strip(),
            "social_facebook": request.form.get("social_facebook", "").strip(),
            "social_instagram": request.form.get("social_instagram", "").strip(),
            "social_twitter": request.form.get("social_twitter", "").strip(),
        }

        conn = get_db()
        for key, value in updates.items():
            if value == "":
                value = DEFAULT_SETTINGS.get(key, "")
            conn.execute(
                """
                INSERT INTO site_settings (key, value)
                VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                (key, value),
            )
        conn.commit()
        conn.close()
        flash("Settings updated.", "success")
        return redirect(url_for("admin_settings"))

    return render_template("admin/settings.html", settings=settings)


@app.route("/admin/inquiries")
@login_required
def admin_inquiries():
    conn = get_db()
    rows = conn.execute(
        """
        SELECT inquiries.*, kittens.name AS kitten_name
        FROM inquiries
        LEFT JOIN kittens ON kittens.id = inquiries.kitten_id
        ORDER BY inquiries.created_at DESC
        """
    ).fetchall()
    conn.close()
    return render_template("admin/inquiries.html", inquiries=rows)


@app.route("/admin/inquiries/<int:inquiry_id>/toggle", methods=["POST"])
@login_required
def admin_inquiries_toggle(inquiry_id):
    conn = get_db()
    row = conn.execute(
        "SELECT status FROM inquiries WHERE id = ?", (inquiry_id,)
    ).fetchone()
    if not row:
        conn.close()
        abort(404)
    new_status = "fulfilled" if row["status"] != "fulfilled" else "open"
    conn.execute(
        "UPDATE inquiries SET status = ? WHERE id = ?", (new_status, inquiry_id)
    )
    conn.commit()
    conn.close()
    flash("Inquiry status updated.", "success")
    return redirect(url_for("admin_inquiries"))


@app.route("/admin/pages/delivery", methods=["GET", "POST"])
@login_required
def admin_delivery_page():
    if request.method == "POST":
        return save_delivery_page()
    page = fetch_page("delivery")
    if page:
        while len(page["steps"]) < 3:
            page["steps"].append({"title": "", "body": ""})
        while len(page["blocks"]) < 4:
            page["blocks"].append({"title": "", "body": "", "image": "", "layout": "left"})
    return render_template("admin/delivery_page.html", page=page)


@app.route("/admin/pages")
@login_required
def admin_pages():
    conn = get_db()
    rows = conn.execute(
        "SELECT slug, title FROM pages WHERE slug != 'delivery' ORDER BY title"
    ).fetchall()
    conn.close()
    return render_template("admin/pages_list.html", pages=rows)


@app.route("/admin/pages/<slug>", methods=["GET", "POST"])
@login_required
def admin_page_edit(slug):
    if slug == "delivery":
        return redirect(url_for("admin_delivery_page"))
    if request.method == "POST":
        return save_generic_page(slug)
    page = fetch_page(slug)
    if not page:
        abort(404)
    while len(page["blocks"]) < 4:
        page["blocks"].append({"title": "", "body": "", "image": "", "layout": "left"})
    return render_template("admin/page_form.html", page=page)


@app.route("/admin/blog")
@login_required
def admin_blog():
    posts = fetch_blog_posts(published_only=False)
    return render_template("admin/blog_list.html", posts=posts)


@app.route("/admin/blog/new", methods=["GET", "POST"])
@login_required
def admin_blog_new():
    if request.method == "POST":
        return save_blog_post()
    return render_template("admin/blog_form.html", post=None, mode="new")


@app.route("/admin/blog/<int:post_id>/edit", methods=["GET", "POST"])
@login_required
def admin_blog_edit(post_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM blog_posts WHERE id = ?", (post_id,)).fetchone()
    conn.close()
    if not row:
        abort(404)
    post = dict(row)
    if request.method == "POST":
        return save_blog_post(post_id)
    return render_template("admin/blog_form.html", post=post, mode="edit")


@app.route("/admin/blog/<int:post_id>/delete", methods=["POST"])
@login_required
def admin_blog_delete(post_id):
    conn = get_db()
    conn.execute("DELETE FROM blog_posts WHERE id = ?", (post_id,))
    conn.commit()
    conn.close()
    flash("Blog post deleted.", "success")
    return redirect(url_for("admin_blog"))


@app.route("/admin/blog/reseed", methods=["POST"])
@login_required
def admin_blog_reseed():
    seed_posts = load_seed_posts()
    conn = get_db()
    conn.execute("DELETE FROM blog_posts")

    max_posts = 50
    current_count = 0
    for post in seed_posts:
        if current_count >= max_posts:
            break
        payload = dict(post)
        base_slug = slugify(payload["title"])
        slug = ensure_unique_slug(conn, base_slug)
        published_at = payload.get("published_at")

        if published_at:
            conn.execute(
                """
                INSERT INTO blog_posts
                (title, slug, excerpt, content, cover_image, meta_title, meta_description, keywords, status, published_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'published', ?)
                """,
                (
                    payload["title"],
                    slug,
                    payload.get("excerpt", ""),
                    payload.get("content", ""),
                    payload.get("cover_image", ""),
                    payload.get("meta_title", ""),
                    payload.get("meta_description", ""),
                    payload.get("keywords", ""),
                    published_at,
                ),
            )
        else:
            conn.execute(
                """
                INSERT INTO blog_posts
                (title, slug, excerpt, content, cover_image, meta_title, meta_description, keywords, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'published')
                """,
                (
                    payload["title"],
                    slug,
                    payload.get("excerpt", ""),
                    payload.get("content", ""),
                    payload.get("cover_image", ""),
                    payload.get("meta_title", ""),
                    payload.get("meta_description", ""),
                    payload.get("keywords", ""),
                ),
            )
        current_count += 1

    conn.commit()
    conn.close()
    flash("Blog posts reseeded from the content library.", "success")
    return redirect(url_for("admin_blog"))

# -------------------- RUN --------------------
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=True)
