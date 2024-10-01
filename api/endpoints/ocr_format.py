import re
import json

def structure_ocr_data(raw_data: str):
    # Clean up the input (removing unnecessary characters like `\n`)
    cleaned_data = raw_data.replace("\\n", "\n").strip()
    
    # Extracting data using regex patterns
    structured_data = {}

    # Extracting name and role
    match_name = re.search(r"/(.+?)/(.+)", cleaned_data)
    if match_name:
        structured_data["name"] = match_name.group(1).strip()
        structured_data["role"] = match_name.group(2).strip()
    
    # Extracting location, phone, email, and LinkedIn
    match_location = re.search(r"LOCATION = \"(.+?)\"", cleaned_data)
    if match_location:
        structured_data["location"] = match_location.group(1)

    match_phone = re.search(r"PHONE = \"(.+?)\"", cleaned_data)
    if match_phone:
        structured_data["phone"] = match_phone.group(1)

    match_email = re.search(r"EMAIL = \"(.+?)\"", cleaned_data)
    if match_email:
        structured_data["email"] = match_email.group(1)

    match_linkedin = re.search(r"LINKEDIN = \"(.+?)\"", cleaned_data)
    if match_linkedin:
        structured_data["linkedin"] = match_linkedin.group(1)

    # Extracting skills
    match_skills = re.search(r"SKILLS = {(.*?)}", cleaned_data, re.DOTALL)
    if match_skills:
        skills_data = match_skills.group(1).split(',')
        structured_data["skills"] = {skill.split(':')[0].strip().strip('"'): float(skill.split(':')[1].strip()) for skill in skills_data}

    # Extracting languages
    match_languages = re.search(r"LANGUAGES = {(.*?)}", cleaned_data, re.DOTALL)
    if match_languages:
        languages_data = match_languages.group(1).split(',')
        structured_data["languages"] = {lang.split(':')[0].strip().strip('"'): lang.split(':')[1].strip().strip('"') for lang in languages_data}

    # Extracting hobbies
    match_hobbies = re.search(r"HOBBIES = \[(.*?)\]", cleaned_data, re.DOTALL)
    if match_hobbies:
        hobbies_data = match_hobbies.group(1).split(',')
        structured_data["hobbies"] = [hobby.strip().strip('"') for hobby in hobbies_data]

    # Extracting career objective
    match_objective = re.search(r"CAREER_OBJECTIVE = \"\"\"(.*?)\"\"\"", cleaned_data, re.DOTALL)
    if match_objective:
        structured_data["career_objective"] = match_objective.group(1).strip()

    # Extracting experience
    match_experience = re.findall(r"Job\((.*?)\)", cleaned_data, re.DOTALL)
    experience_list = []
    for exp in match_experience:
        exp_data = {}
        exp_data["start"] = re.search(r"start=\"(.+?)\"", exp).group(1)
        exp_data["end"] = re.search(r"end=(None|\".+?\")", exp).group(1).strip('"') or None
        exp_data["position"] = re.search(r"position=\"(.+?)\"", exp).group(1)
        exp_data["place"] = re.search(r"place=\"(.+?)\"", exp).group(1)
        exp_data["achievements"] = re.findall(r"\"(.+?)\"", exp)
        experience_list.append(exp_data)
    structured_data["experience"] = experience_list

    # Extracting education
    match_education = re.findall(r"(Study|Certification)\((.*?)\)", cleaned_data)
    education_list = []
    for edu_type, edu_details in match_education:
        edu_data = {}
        if edu_type == "Study":
            edu_info = edu_details.split(',')
            edu_data["start"] = edu_info[0].strip().strip('"')
            edu_data["institution"] = edu_info[1].strip().strip('"')
            edu_data["degree"] = edu_info[2].strip().strip('"')
            edu_data["level"] = edu_info[3].strip().strip('"')
        else:  # Certification
            edu_data["certification"] = edu_details.strip().strip('"')
        education_list.append(edu_data)
    structured_data["education"] = education_list

    return json.dumps(structured_data, indent=4)