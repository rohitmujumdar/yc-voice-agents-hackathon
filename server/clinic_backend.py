"""Mock backend data for Cora — clinic receptionist voice agent.

Departments, doctors, schedule, and known patients for the demo.
All lookups are mocked. Replace with real backend calls as needed.
"""

DEPARTMENTS = {
    "scheduling": {
        "name": "Scheduling",
        "hours": "Mon-Fri 8am-5pm",
        "description": "Book, reschedule, or cancel appointments",
        "keywords": ["appointment", "book", "schedule", "reschedule", "cancel", "available", "slot", "see the doctor", "check-up", "visit", "come in"],
    },
    "billing": {
        "name": "Billing",
        "hours": "Mon-Fri 9am-4pm",
        "description": "Insurance, charges, payments, and statements",
        "keywords": ["bill", "charge", "payment", "insurance", "copay", "statement", "owe", "cost", "price", "pay", "claim", "denied", "coverage"],
    },
    "pharmacy": {
        "name": "Pharmacy / Rx Refills",
        "hours": "Mon-Fri 8am-6pm",
        "description": "Prescription refills, medication questions",
        "keywords": ["prescription", "refill", "medication", "medicine", "drug", "dosage", "pharmacy", "rx", "pills", "ran out"],
    },
    "nurse_line": {
        "name": "Nurse Line",
        "hours": "24/7",
        "description": "Medical questions, symptoms, side effects",
        "keywords": ["symptom", "sick", "pain", "fever", "side effect", "reaction", "feeling", "hurt", "cough", "nausea", "dizzy", "medical question", "advice"],
    },
    "records": {
        "name": "Medical Records",
        "hours": "Mon-Fri 9am-4pm",
        "description": "Request, transfer, or update medical records",
        "keywords": ["records", "paperwork", "forms", "transfer", "release", "copy", "chart", "history", "documents"],
    },
}

DOCTORS = {
    "dr. chen": {
        "name": "Dr. Sarah Chen",
        "specialty": "Family Medicine",
        "available_days": ["Monday", "Tuesday", "Wednesday", "Thursday"],
    },
    "dr. patel": {
        "name": "Dr. Raj Patel",
        "specialty": "Internal Medicine",
        "available_days": ["Monday", "Wednesday", "Friday"],
    },
    "dr. williams": {
        "name": "Dr. Maria Williams",
        "specialty": "Pediatrics",
        "available_days": ["Tuesday", "Thursday", "Friday"],
    },
    "dr. nakamura": {
        "name": "Dr. Ken Nakamura",
        "specialty": "Family Medicine",
        "available_days": ["Monday", "Tuesday", "Friday"],
    },
}

AVAILABLE_SLOTS = {
    "Monday": ["9:00 AM", "10:30 AM", "2:00 PM", "3:30 PM"],
    "Tuesday": ["8:30 AM", "11:00 AM", "1:00 PM", "4:00 PM"],
    "Wednesday": ["9:00 AM", "10:00 AM", "2:30 PM"],
    "Thursday": ["8:30 AM", "11:30 AM", "3:00 PM", "4:30 PM"],
    "Friday": ["9:00 AM", "10:30 AM", "1:00 PM", "2:00 PM"],
}

KNOWN_PATIENTS = {
    "+14155551234": {
        "name": "Alex Rivera",
        "dob": "03/15/1988",
        "doctor": "dr. chen",
        "last_visit": "April 10, 2026",
    },
    "+14155555678": {
        "name": "Jordan Kim",
        "dob": "11/22/1975",
        "doctor": "dr. patel",
        "last_visit": "May 2, 2026",
    },
}
