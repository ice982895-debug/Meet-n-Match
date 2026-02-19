import json
import random
import uuid

# Updated Configuration for larger dataset
NUM_MENTORS = 1000 
NUM_MENTEES = 100

# Expanded Category Data
CATEGORIES = {
    "Tech": {
        "titles": [
            "Product Designer", "Senior Product Designer", "UX Researcher", 
            "Frontend Developer", "Backend Engineer", "Full Stack Developer",
            "Data Scientist", "Machine Learning Engineer", "Product Manager",
            "DevOps Engineer", "Cloud Architect", "Cybersecurity Analyst"
        ],
        "tools": [
            "Figma", "React", "Python", "Node.js", "AWS", "Docker", "Kubernetes",
            "Terraform", "PostgreSQL", "TensorFlow", "Jira", "GitHub"
        ],
        "interests": [
            "AI/ML", "Scalability", "Design Systems", "Open Source", "Startup Culture",
            "Blockchain", "Cloud Native", "Accessibility"
        ]
    },
    "Healthcare": {
        "titles": [
            "Clinical Psychologist", "Surgeon", "Registered Nurse", "Pediatrician",
            "Pharmacist", "Medical Researcher", "Health Administrator", "Physical Therapist",
            "Nutritionist", "Radiologist"
        ],
        "tools": [
            "Epic Systems", "Cerner", "SPSS", "Stethoscope", "MRI Tech",
            "Telehealth Platforms", "Meditech", "RedCap"
        ],
        "interests": [
            "Patient Care", "Medical Etihcs", "Public Health", "Clinical Research",
            "Mental Health Awareness", "Health Equity", "Telemedicine"
        ]
    },
    "Education": {
        "titles": [
            "High School Teacher", "University Professor", "Curriculum Developer",
            "Special Education Teacher", "Educational Consultant", "School Counselor",
            "Principal", "Instructional Designer"
        ],
        "tools": [
            "Canvas", "Blackboard", "Google Classroom", "Zoom", "Kahoot",
            "Smartboard", "Moodle"
        ],
        "interests": [
            "Student Engagement", "EdTech", "Special Education", "Curriculum Design",
            "Lifelong Learning", "Educational Policy", "Literacy"
        ]
    },
    "Arts & Creative": {
        "titles": [
            "Music Producer", "Graphic Designer", "Fine Artist", "Creative Director",
            "Film Editor", "Sound Engineer", "Animator", "Fashion Designer",
            "Photographer", "Interior Designer"
        ],
        "tools": [
            "Adobe Creative Suite", "Pro Tools", "Logic Pro", "Blender", "Maya",
            "Final Cut Pro", "SketchUp", "Ableton Live"
        ],
        "interests": [
            "Visual Storytelling", "Music Theory", "Sustainable Fashion", "Animation",
            "Digital Art", "Cinematography", "Acoustics"
        ]
    },
    "Business & Law": {
        "titles": [
            "Corporate Lawyer", "Financial Analyst", "Marketing Manager", "HR Specialist",
            "Project Manager", "Accountant", "Business Consultant", "Investment Banker"
        ],
        "tools": [
            "Excel", "Salesforce", "Tableau", "QuickBooks", "Power BI",
            "Asana", "LexisNexis"
        ],
        "interests": [
            "Financial Planning", "Corporate Strategy", "Intellectual Property",
            "Market Research", "Organizational Psychology", "Leadership"
        ]
    }
}

BIOS = [
    "Passionate about making a difference in the field.",
    "Dedicated to continuous learning and improvement.",
    "Experienced professional with a proven track record.",
    "Love mentoring and sharing knowledge with the next generation.",
    "Focused on innovation and creative problem solving.",
    "Believer in collaboration and team success.",
    "Striving for excellence in every project.",
    "Expert in navigating complex challenges."
]

def generate_user(role, min_exp, max_exp):
    """Generates a random user dictionary from a random category."""
    category_name = random.choice(list(CATEGORIES.keys()))
    category_data = CATEGORIES[category_name]
    
    job = random.choice(category_data["titles"])
    
    # Add seniority prefixes
    if role == "Mentor":
        if "Senior" not in job and "Lead" not in job and "Manager" not in job and "Director" not in job and "Professor" not in job:
             if random.random() > 0.4:
                 job = f"Senior {job}"
    elif role == "Mentee":
        if random.random() > 0.5:
            job = f"Junior {job}"
        elif random.random() > 0.8:
            job = f"Aspiring {job}"
    
    # Ensure tool list isn't larger than available tools
    num_tools = min(len(category_data["tools"]), random.randint(2, 5))
    
    return {
        "user_id": str(uuid.uuid4()),
        "role": role,
        "job_title": job,
        "field": category_name, # Added field for reference
        "tools": random.sample(category_data["tools"], k=num_tools),
        "years_of_experience": random.randint(min_exp, max_exp),
        "interests": random.sample(category_data["interests"], k=random.randint(2, 4)),
        "bio": f"{random.choice(BIOS)} {random.choice(BIOS)} specializing in {category_name}."
    }

def main():
    print(f"Generating {NUM_MENTORS} mentors and {NUM_MENTEES} mentees across {len(CATEGORIES)} fields...")
    
    mentors = [generate_user("Mentor", min_exp=5, max_exp=30) for _ in range(NUM_MENTORS)]
    mentees = [generate_user("Mentee", min_exp=0, max_exp=5) for _ in range(NUM_MENTEES)]
    
    with open("mentors.json", "w") as f:
        json.dump(mentors, f, indent=2)
    print("Created mentors.json")
    
    with open("mentees.json", "w") as f:
        json.dump(mentees, f, indent=2)
    print("Created mentees.json")

if __name__ == "__main__":
    main()
