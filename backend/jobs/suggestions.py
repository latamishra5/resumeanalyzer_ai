"""Module containing job-related data and configurations using Material icon tokens."""

# Job titles and skills suggestions
JOB_SUGGESTIONS = [
    {"text": "Software Engineer", "icon": ":material/code:"},
    {"text": "Full Stack Developer", "icon": ":material/layers:"},
    {"text": "Data Scientist", "icon": ":material/analytics:"},
    {"text": "Product Manager", "icon": ":material/inventory_2:"},
    {"text": "DevOps Engineer", "icon": ":material/settings:"},
    {"text": "UI/UX Designer", "icon": ":material/palette:"},
    {"text": "Python Developer", "icon": ":material/terminal:"},
    {"text": "Java Developer", "icon": ":material/coffee:"},
    {"text": "React Developer", "icon": ":material/web:"},
    {"text": "Machine Learning Engineer", "icon": ":material/smart_toy:"},
    {"text": "Backend Developer", "icon": ":material/dns:"},
    {"text": "Frontend Developer", "icon": ":material/web_asset:"},
    {"text": "Node.js Developer", "icon": ":material/hub:"},
    {"text": "Angular Developer", "icon": ":material/web:"},
    {"text": "PHP Developer", "icon": ":material/code:"},
    {"text": "Ruby Developer", "icon": ":material/diamond:"},
    {"text": "Go Developer", "icon": ":material/speed:"},
    {"text": "C++ Developer", "icon": ":material/memory:"},
    {"text": "C# Developer", "icon": ":material/sports_esports:"},
    {"text": "Django Developer", "icon": ":material/build:"},
    {"text": "Data Analyst", "icon": ":material/insights:"},
    {"text": "Big Data Engineer", "icon": ":material/storage:"},
    {"text": "Database Administrator", "icon": ":material/database:"},
    {"text": "Business Intelligence Analyst", "icon": ":material/bar_chart:"},
    {"text": "Cloud Engineer", "icon": ":material/cloud:"},
    {"text": "AWS Engineer", "icon": ":material/cloud_queue:"},
    {"text": "Azure Engineer", "icon": ":material/cloud_done:"},
    {"text": "Google Cloud Engineer", "icon": ":material/cloud_sync:"},
    {"text": "Network Engineer", "icon": ":material/lan:"},
    {"text": "AI Researcher", "icon": ":material/psychology:"},
    {"text": "NLP Engineer", "icon": ":material/translate:"},
    {"text": "Computer Vision Engineer", "icon": ":material/visibility:"},
    {"text": "Deep Learning Engineer", "icon": ":material/neurology:"},
    {"text": "Cybersecurity Analyst", "icon": ":material/lock:"},
    {"text": "Ethical Hacker", "icon": ":material/security:"},
    {"text": "Security Engineer", "icon": ":material/verified_user:"},
    {"text": "Penetration Tester", "icon": ":material/bug_report:"},
    {"text": "Cryptography Engineer", "icon": ":material/key:"},
    {"text": "Game Developer", "icon": ":material/sports_esports:"},
    {"text": "Embedded Systems Engineer", "icon": ":material/developer_board:"},
    {"text": "Mobile App Developer", "icon": ":material/smartphone:"},
    {"text": "iOS Developer", "icon": ":material/phone_iphone:"},
    {"text": "Android Developer", "icon": ":material/android:"},
    {"text": "Blockchain Developer", "icon": ":material/link:"},
    {"text": "IoT Developer", "icon": ":material/sensors:"},
    {"text": "AR/VR Developer", "icon": ":material/view_in_ar:"},
    {"text": "Project Manager", "icon": ":material/assignment:"},
    {"text": "Technical Writer", "icon": ":material/edit_note:"},
    {"text": "QA Engineer", "icon": ":material/check_circle:"},
    {"text": "Scrum Master", "icon": ":material/sync:"},
    {"text": "Support Engineer", "icon": ":material/support_agent:"},
    {"text": "IT Consultant", "icon": ":material/business_center:"},
    {"text": "Technical Support Specialist", "icon": ":material/headset_mic:"},
]


# Location suggestions - organized by states and major cities
LOCATION_SUGGESTIONS = [
    # Work modes
    {"text": "Remote", "icon": ":material/home_work:", "type": "work_mode"},
    {"text": "Work from Home", "icon": ":material/home:", "type": "work_mode"},
    {"text": "Hybrid", "icon": ":material/apartment:", "type": "work_mode"},

    # Major tech hubs
    {"text": "Bangalore", "icon": ":material/location_on:", "type": "city", "state": "Karnataka"},
    {"text": "Mumbai", "icon": ":material/location_on:", "type": "city", "state": "Maharashtra"},
    {"text": "Delhi", "icon": ":material/location_on:", "type": "city", "state": "Delhi"},
    {"text": "Hyderabad", "icon": ":material/location_on:", "type": "city", "state": "Telangana"},
    {"text": "Pune", "icon": ":material/location_on:", "type": "city", "state": "Maharashtra"},
    {"text": "Chennai", "icon": ":material/location_on:", "type": "city", "state": "Tamil Nadu"},
    {"text": "Noida", "icon": ":material/location_on:", "type": "city", "state": "Uttar Pradesh"},
    {"text": "Gurgaon", "icon": ":material/location_on:", "type": "city", "state": "Haryana"},

    # States
    {"text": "Karnataka", "icon": ":material/map:", "type": "state"},
    {"text": "Maharashtra", "icon": ":material/map:", "type": "state"},
    {"text": "Tamil Nadu", "icon": ":material/map:", "type": "state"},
    {"text": "Telangana", "icon": ":material/map:", "type": "state"},
    {"text": "Delhi", "icon": ":material/map:", "type": "state"},
    {"text": "Uttar Pradesh", "icon": ":material/map:", "type": "state"},
    {"text": "Gujarat", "icon": ":material/map:", "type": "state"},
    {"text": "Rajasthan", "icon": ":material/map:", "type": "state"},
    {"text": "Kerala", "icon": ":material/map:", "type": "state"},
    {"text": "West Bengal", "icon": ":material/map:", "type": "state"},
    {"text": "Punjab", "icon": ":material/map:", "type": "state"},
    {"text": "Haryana", "icon": ":material/map:", "type": "state"},
    {"text": "Andhra Pradesh", "icon": ":material/map:", "type": "state"},
    {"text": "Madhya Pradesh", "icon": ":material/map:", "type": "state"},
    {"text": "Bihar", "icon": ":material/map:", "type": "state"},

    # Karnataka cities
    {"text": "Mysore", "icon": ":material/location_on:", "type": "city", "state": "Karnataka"},
    {"text": "Hubli", "icon": ":material/location_on:", "type": "city", "state": "Karnataka"},
    {"text": "Mangalore", "icon": ":material/location_on:", "type": "city", "state": "Karnataka"},
    {"text": "Belgaum", "icon": ":material/location_on:", "type": "city", "state": "Karnataka"},
    {"text": "Davangere", "icon": ":material/location_on:", "type": "city", "state": "Karnataka"},

    # Maharashtra cities
    {"text": "Nagpur", "icon": ":material/location_on:", "type": "city", "state": "Maharashtra"},
    {"text": "Nashik", "icon": ":material/location_on:", "type": "city", "state": "Maharashtra"},
    {"text": "Aurangabad", "icon": ":material/location_on:", "type": "city", "state": "Maharashtra"},
    {"text": "Kolhapur", "icon": ":material/location_on:", "type": "city", "state": "Maharashtra"},
    {"text": "Solapur", "icon": ":material/location_on:", "type": "city", "state": "Maharashtra"},

    # Tamil Nadu cities
    {"text": "Coimbatore", "icon": ":material/location_on:", "type": "city", "state": "Tamil Nadu"},
    {"text": "Madurai", "icon": ":material/location_on:", "type": "city", "state": "Tamil Nadu"},
    {"text": "Salem", "icon": ":material/location_on:", "type": "city", "state": "Tamil Nadu"},
    {"text": "Tiruchirappalli", "icon": ":material/location_on:", "type": "city", "state": "Tamil Nadu"},
    {"text": "Vellore", "icon": ":material/location_on:", "type": "city", "state": "Tamil Nadu"},

    # Uttar Pradesh cities
    {"text": "Lucknow", "icon": ":material/location_on:", "type": "city", "state": "Uttar Pradesh"},
    {"text": "Kanpur", "icon": ":material/location_on:", "type": "city", "state": "Uttar Pradesh"},
    {"text": "Agra", "icon": ":material/location_on:", "type": "city", "state": "Uttar Pradesh"},
    {"text": "Varanasi", "icon": ":material/location_on:", "type": "city", "state": "Uttar Pradesh"},
    {"text": "Meerut", "icon": ":material/location_on:", "type": "city", "state": "Uttar Pradesh"},

    # Andhra Pradesh cities
    {"text": "Vijayawada", "icon": ":material/location_on:", "type": "city", "state": "Andhra Pradesh"},
    {"text": "Visakhapatnam", "icon": ":material/location_on:", "type": "city", "state": "Andhra Pradesh"},
    {"text": "Tirupati", "icon": ":material/location_on:", "type": "city", "state": "Andhra Pradesh"},
    {"text": "Guntur", "icon": ":material/location_on:", "type": "city", "state": "Andhra Pradesh"},
    {"text": "Nellore", "icon": ":material/location_on:", "type": "city", "state": "Andhra Pradesh"},

    # West Bengal cities
    {"text": "Kolkata", "icon": ":material/location_on:", "type": "city", "state": "West Bengal"},
    {"text": "Darjeeling", "icon": ":material/location_on:", "type": "city", "state": "West Bengal"},
    {"text": "Siliguri", "icon": ":material/location_on:", "type": "city", "state": "West Bengal"},
    {"text": "Durgapur", "icon": ":material/location_on:", "type": "city", "state": "West Bengal"},
    {"text": "Asansol", "icon": ":material/location_on:", "type": "city", "state": "West Bengal"},

    # Gujarat cities
    {"text": "Ahmedabad", "icon": ":material/location_on:", "type": "city", "state": "Gujarat"},
    {"text": "Surat", "icon": ":material/location_on:", "type": "city", "state": "Gujarat"},
    {"text": "Vadodara", "icon": ":material/location_on:", "type": "city", "state": "Gujarat"},
    {"text": "Rajkot", "icon": ":material/location_on:", "type": "city", "state": "Gujarat"},
    {"text": "Bhavnagar", "icon": ":material/location_on:", "type": "city", "state": "Gujarat"},

    # Rajasthan cities
    {"text": "Jaipur", "icon": ":material/location_on:", "type": "city", "state": "Rajasthan"},
    {"text": "Jodhpur", "icon": ":material/location_on:", "type": "city", "state": "Rajasthan"},
    {"text": "Udaipur", "icon": ":material/location_on:", "type": "city", "state": "Rajasthan"},
    {"text": "Kota", "icon": ":material/location_on:", "type": "city", "state": "Rajasthan"},
    {"text": "Ajmer", "icon": ":material/location_on:", "type": "city", "state": "Rajasthan"},

    # Kerala cities
    {"text": "Kochi", "icon": ":material/location_on:", "type": "city", "state": "Kerala"},
    {"text": "Thiruvananthapuram", "icon": ":material/location_on:", "type": "city", "state": "Kerala"},
    {"text": "Kozhikode", "icon": ":material/location_on:", "type": "city", "state": "Kerala"},
    {"text": "Thrissur", "icon": ":material/location_on:", "type": "city", "state": "Kerala"},
    {"text": "Alappuzha", "icon": ":material/location_on:", "type": "city", "state": "Kerala"},

    # Punjab cities
    {"text": "Amritsar", "icon": ":material/location_on:", "type": "city", "state": "Punjab"},
    {"text": "Ludhiana", "icon": ":material/location_on:", "type": "city", "state": "Punjab"},
    {"text": "Jalandhar", "icon": ":material/location_on:", "type": "city", "state": "Punjab"},
    {"text": "Patiala", "icon": ":material/location_on:", "type": "city", "state": "Punjab"},
    {"text": "Bathinda", "icon": ":material/location_on:", "type": "city", "state": "Punjab"},

    # Haryana cities
    {"text": "Faridabad", "icon": ":material/location_on:", "type": "city", "state": "Haryana"},
    {"text": "Panipat", "icon": ":material/location_on:", "type": "city", "state": "Haryana"},
    {"text": "Ambala", "icon": ":material/location_on:", "type": "city", "state": "Haryana"},
    {"text": "Karnal", "icon": ":material/location_on:", "type": "city", "state": "Haryana"},
    {"text": "Hisar", "icon": ":material/location_on:", "type": "city", "state": "Haryana"},

    # Northeast cities
    {"text": "Guwahati", "icon": ":material/location_on:", "type": "city", "state": "Assam"},
    {"text": "Shillong", "icon": ":material/location_on:", "type": "city", "state": "Meghalaya"},
    {"text": "Imphal", "icon": ":material/location_on:", "type": "city", "state": "Manipur"},
    {"text": "Aizawl", "icon": ":material/location_on:", "type": "city", "state": "Mizoram"},
    {"text": "Gangtok", "icon": ":material/location_on:", "type": "city", "state": "Sikkim"},

    # Union Territories
    {"text": "Chandigarh", "icon": ":material/location_on:", "type": "city", "state": "Chandigarh"},
    {"text": "Port Blair", "icon": ":material/location_on:", "type": "city", "state": "Andaman and Nicobar Islands"},
    {"text": "Shimla", "icon": ":material/location_on:", "type": "city", "state": "Himachal Pradesh"},
    {"text": "Dehradun", "icon": ":material/location_on:", "type": "city", "state": "Uttarakhand"},
    {"text": "Itanagar", "icon": ":material/location_on:", "type": "city", "state": "Arunachal Pradesh"},
]


def get_cities_by_state(state_name):
    """Get list of cities for a specific state."""
    return [loc for loc in LOCATION_SUGGESTIONS if loc.get("type") == "city" and loc.get("state") == state_name]


def get_all_states():
    """Get list of all states."""
    return [loc for loc in LOCATION_SUGGESTIONS if loc.get("type") == "state"]


JOB_TYPES = [
    {"id": "all", "text": "All Types"},
    {"id": "full-time", "text": "Full Time"},
    {"id": "part-time", "text": "Part Time"},
    {"id": "contract", "text": "Contract"},
    {"id": "internship", "text": "Internship"},
    {"id": "remote", "text": "Remote"},
]

EXPERIENCE_RANGES = [
    {"id": "all", "text": "All Levels"},
    {"id": "fresher", "text": "Fresher"},
    {"id": "1-3", "text": "1-3 years"},
    {"id": "3-5", "text": "3-5 years"},
    {"id": "5-7", "text": "5-7 years"},
    {"id": "7+", "text": "7+ years"},
]

SALARY_RANGES = [
    {"id": "all", "text": "All Ranges"},
    {"id": "0-3", "text": "0-3 LPA"},
    {"id": "3-6", "text": "3-6 LPA"},
    {"id": "6-10", "text": "6-10 LPA"},
    {"id": "10-15", "text": "10-15 LPA"},
    {"id": "15+", "text": "15+ LPA"},
]
