# Contains the routes related to the main functionality

import json
import math
import os
import time
from flask import render_template, request, redirect, url_for, jsonify, session, current_app, flash
from .. import db, mail
from ..models import Interview, InterviewParameter, Session, Question, Answer, Result, HR, Applicant, Company, Review, ReviewQuestion, Thread 
from ..openai_utils import create_openai_thread, get_openai_thread_response, get_thank_you_message, create_scoring_thread
from flask_jwt_extended import jwt_required, get_jwt_identity, set_access_cookies
from ..forms import ReviewForm, RatingForm
from flask import Blueprint
from datetime import datetime
from flask_mail import Message
from helpers import get_url, get_color
from ..TTS_utils import generate_voice
from ..STT_utils import get_transcription_result
import boto3




main = Blueprint('main', __name__)


### USEFUL METHOD

def get_interview_conversation(session_id):
    # Retrieve all questions and answers for the session
    questions = Question.query.filter_by(session_id=session_id).all()
    answers = Answer.query.filter_by(session_id=session_id).all()

    # Initialize conversation list
    conversation = []

    # Iterate through questions and answers, assuming they are in order
    for i in range(max(len(questions), len(answers))):
        if i < len(questions):
            conversation.append({'role': 'Q', 'content': questions[i].content})
        if i < len(answers):
            conversation.append({'role': 'A', 'content': answers[i].content})

    return conversation


def upload_audio_to_s3(file_path):
    s3 = boto3.client('s3')
    bucket_name = 'votre-nom-de-bucket'
    object_name = file_path.split('/')[-1]
    s3.upload_file(file_path, bucket_name, object_name)
    return f's3://{bucket_name}/{object_name}'


@main.route('/transcribe-audio', methods=['POST'])
def transcribe_audio():
    # Save the uploaded audio file
    audio_file = request.files['audio']
    file_path = os.path.join('path/to/save/audio', audio_file.filename)
    audio_file.save(file_path)

    # Upload audio file to S3 and get the URI
    s3_uri = upload_audio_to_s3(file_path)

    # Use AWS Transcribe to get transcription
    job_name = f"transcription_{int(time.time())}"
    transcribe_audio(s3_uri, job_name)

    # Poll AWS Transcribe until job completes and get the transcription result
    transcription_text = get_transcription_result(job_name)

    return jsonify({'transcription': transcription_text})



######### HR ROUTES 
@main.route('/home/<int:hr_id>')
@jwt_required()
def home(hr_id):
    current_user = get_jwt_identity()  # Retrieve the user identity from the JWT
    if current_user["hr_id"] != hr_id:  # Ensure the JWT identity matches the requested hr_id
        return jsonify({"msg": "Unauthorized access."}), 403
    
    hr = HR.query.get_or_404(hr_id)
    if not hr:
        return redirect(url_for('auth.login'))
    
    interviews = Interview.query.filter_by(hr_id=hr_id).all()
    interview_data = []

    total_sessions = 0
    total_applicants_set = set()

    for interview in interviews:
        interview_parameters = InterviewParameter.query.filter_by(interview_id=interview.id).first()
        if not interview_parameters:
            continue  # Skip if no interview parameters are found

        sessions = Session.query.filter_by(interview_parameter_id=interview_parameters.id).all()
        session_data = []
        for session in sessions:
            applicant = Applicant.query.get(session.applicant_id)
            result = Result.query.filter_by(session_id=session.id).first()
            if not result or not result.score_interview or not result.score_interview.get('criteria_score'):
                continue  # Skip sessions with no results, no score_interview, or no criteria scores

            criteria_scores = result.score_interview['criteria_score']

            criteria_keys = [
                'communication_skills',
                'logical_reasoning_and_structure_and_problem_solving',
                'creativity',
                'business_acumen',
                'analytical_skills',
                'project_management_and_prioritization'
            ]

             # Retrieve the criteria values
            criteria_value = [criteria_scores.get(key, 0) for key in criteria_keys]

            # Load the ponderation from the interview parameters
            situations = json.loads(interview_parameters.situation) if interview_parameters.situation else []
            ponderation = json.loads(interview_parameters.ponderation) if interview_parameters.ponderation else [[1, 1, 1, 1, 1, 1] for _ in range(len(situations))]


            # Calculate the weighted criteria values
            weighted_criteria_values = [criteria_value[i] * ponderation[0][i] for i in range(len(criteria_value))]


            mean_score = sum(weighted_criteria_values) / (sum(ponderation[0]))

            if mean_score is None:
                continue  # Skip if mean score is None

            session_data.append({
                'applicant_name': applicant.name,
                'applicant_surname': applicant.surname,
                'applicant_email': applicant.email_address,
                'start_time': session.start_time,
                'score': criteria_scores,
                'mean_score': mean_score,
                'id': session.id,
            })
            total_applicants_set.add(applicant.email_address)
        interview_data.append({
            'created_at': interview_parameters.start_time,
            'interview_name' : interview.name,
            'industry': interview_parameters.industry,
            'role': interview_parameters.role,            
            'subrole': interview_parameters.subrole,
            'situation': interview_parameters.get_situations(),
            'language': interview_parameters.language,
            'duration': interview_parameters.duration,
            'max_questions': interview_parameters.max_questions,
            'sessions_count': len(sessions),
            'interview_parameter_id': interview_parameters.id,
            'interview_id': interview_parameters.id,
            'sessions': session_data
        })

        total_sessions += len(sessions)

    total_interviews = len(interviews) 
    total_applicants = len(total_applicants_set)

    return render_template('hr/hr_homepage.html', hr_name=hr.name, hr_surname=hr.surname, company_name=hr.company.name,
                            hr_id=hr.id, interview_data=interview_data, total_interviews=total_interviews,
                           total_sessions=total_sessions, total_applicants=total_applicants, get_color=get_color, get_url=get_url)



@main.route('/create_interview/<int:hr_id>', methods=['GET', 'POST'])
@jwt_required()
def create_interview(hr_id):
    try:
        if request.method == 'POST':
            # Extract fields from form data
            language = request.form.get('language')
            position = request.form.get('position')
            role = "Sales"  # Hardcoded as per your original code
            subrole = request.form.get('subrole')
            industry = request.form.get('industry')
            duration = int(request.form.get('duration', 0))  # Default to 0 if duration is not provided
            situations = request.form.getlist('situations')  # Get situations as a list
            
            if industry == "Other":
                industry = request.form.get('other_industry', '').strip()
                if not industry:
                    return jsonify({"msg": "Please specify the industry if 'Other' is selected."}), 400

            # Load the JSON file to get the ponderation
            json_path = os.path.join(current_app.root_path, 'interview_situations_v4.json')
            with open(json_path) as f:
                interview_situations = json.load(f)

            ponderations = []
            for situation in situations:
                default_ponderation = interview_situations.get(role, {}).get(subrole, {}).get(situation, [3, 3, 3, 3, 3])
                custom_ponderation = [
                    int(request.form.get(f'ponderation_{i+1}', default_ponderation[i]))
                    for i in range(6)
                ]
                custom_ponderation = [1 + (int(custom_ponderation[i]) - 3) * 0.1 for i in range(len(custom_ponderation))]
                ponderations.append(custom_ponderation)

            # Use default ponderation if no situations are selected
            if not situations:
                ponderations = [[1, 1, 1, 1, 1, 1]]

            # Create and save the interview and its parameters
            new_interview = Interview(hr_id=hr_id, name=position)
            db.session.add(new_interview)
            db.session.commit()

            interview_parameter = InterviewParameter(
                language=language,
                role=role,
                subrole=subrole,
                industry=industry,
                duration=duration,
                situation=json.dumps(situations),  # Store situations as JSON string
                ponderation=json.dumps(ponderations),  # Store ponderations as JSON string
                interview_id=new_interview.id
            )

            db.session.add(interview_parameter)
            db.session.commit()

            # Redirect to the interview generated page
            return redirect(url_for('main.interview_generated', interview_parameter_id=interview_parameter.id, hr_id=hr_id))

        # Handle GET request (render the form)
        else:
            json_path = os.path.join(current_app.root_path, 'interview_situations_v4.json')

            with open(json_path) as f:
                interview_situations = json.load(f)

            return render_template('hr/create_interview.html', hr_id=hr_id, interview_situations=interview_situations)

    except Exception as e:
        current_app.logger.error(f"Error in create_interview: {str(e)}")
        return jsonify({"msg": "An error occurred on the server. Please try again."}), 500

    

@main.route('/interview_generated/<int:hr_id>/<int:interview_parameter_id>', methods=['GET', 'POST'])
@jwt_required()
def interview_generated(hr_id,interview_parameter_id):
    interview_parameter = InterviewParameter.query.get_or_404(interview_parameter_id)
    situation = json.loads(interview_parameter.situation)
    interview = Interview.query.get(interview_parameter.interview_id)
    hr = HR.query.get_or_404(hr_id)
    interview_parameter = InterviewParameter.query.get_or_404(interview_parameter_id)
    interview_link = get_url('main.applicant_home', hr_id=hr_id, interview_parameter_id=interview_parameter_id)
    return render_template('hr/interview_generated.html', interview_link=interview_link, hr_id=hr_id, hr= hr, interview_parameter=interview_parameter, interview=interview, situation = situation)


@main.route('/session_details/<int:hr_id>/<int:session_id>', methods=['GET'])
@jwt_required()
def session_details(hr_id, session_id):
    session = Session.query.get(session_id)
    if not session:
        flash("Failed to retrieve interview thread. Please try again.", "danger")
        return redirect(url_for('main.home', hr_id=hr_id))

    applicant = Applicant.query.get_or_404(session.applicant_id)
    questions = Question.query.filter_by(session_id=session_id).all()
    answers = Answer.query.filter_by(session_id=session_id).all()
    nb_questions = len(questions)
    nb_answers = len(answers)
    result = Result.query.filter_by(session_id=session_id).first()
    interview_parameter = InterviewParameter.query.get(session.interview_parameter_id)
    interview = Interview.query.get(interview_parameter.interview_id)

    conversation = get_interview_conversation(session_id)
    # Load criteria scores from the JSON string
    score_interview = result.score_interview

    criteria_scores = result.score_interview['criteria_score']

    criteria_keys = [
        'communication_skills',
        'logical_reasoning_and_structure_and_problem_solving',
        'creativity',
        'business_acumen',
        'analytical_skills',
        'project_management_and_prioritization'
    ]


    # Load the ponderation from the interview parameters
    situations = json.loads(interview_parameter.situation) if interview_parameter.situation else []
    ponderation = json.loads(interview_parameter.ponderation) if interview_parameter.ponderation else [[1, 1, 1, 1, 1, 1] for _ in range(len(situations))]

    # Map the ponderation values to importance descriptions
    ponderation_map = {
        1.2: 'Very important',
        1.1: 'Important',
        1.0: 'Moderately important',
        0.9: 'Slightly important',
        0.8: 'Not important'
    }

    # Map the ponderation values to star ratings
    star_rating_map = {
        1.2: '★★★★★',
        1.1: '★★★★☆',
        1.0: '★★★☆☆',
        0.9: '★★☆☆☆',
        0.8: '★☆☆☆☆'
    }
    criteria_importance = [(criteria_keys[i], star_rating_map.get(ponderation[0][i], '☆☆☆☆☆')) for i in range(len(criteria_keys))]




    return render_template('hr/session_details.html',
                           criteria_importance=criteria_importance,
                           hr_id=hr_id,    
                           session=session,
                           applicant=applicant,
                           conversation=conversation,
                           result=result,
                           interview_parameter=interview_parameter,
                           interview = interview,
                           score_interview = score_interview,
                           nb_answers = nb_answers,
                           nb_questions = nb_questions)


@main.route('/comparison_details/<int:hr_id>/<int:interview_id>', methods=['GET'])
@jwt_required()
def comparison_details(hr_id, interview_id):
    hr = HR.query.get_or_404(hr_id)
    interview = Interview.query.get_or_404(interview_id)
    interview_name = interview.name
    interview_parameters = InterviewParameter.query.filter_by(interview_id=interview_id).first()
    sessions = Session.query.filter_by(interview_parameter_id=interview_parameters.id).all()
    comparison_data = []
    for session in sessions:
        applicant = Applicant.query.get(session.applicant_id)
        result = Result.query.filter_by(session_id=session.id).first()
        nb_answers = len(Answer.query.filter_by(session_id=session.id).all())
        nb_questions = len(Question.query.filter_by(session_id=session.id).all())
        
        if result and result.score_interview:
            criteria_score = result.score_interview.get("criteria_score")
            if criteria_score:
                mean_score = sum(criteria_score.values()) / len(criteria_score)
                comparison_data.append({
                    'applicant_name': applicant.name,
                    'applicant_surname': applicant.surname,
                    'applicant_email': applicant.email_address,
                    'criteria_scores': criteria_score,
                    'mean_score': mean_score,
                    'nb_questions':nb_questions,
                    'nb_answers':nb_answers,
                    'id': session.id  # Add session id here
                
                })

    return render_template('hr/comparison_details.html',
                           hr=hr,
                           hr_id=hr_id,
                           interview_parameters=interview_parameters,
                           interview_name = interview_name,
                           comparison_data=comparison_data,
                           get_color=get_color)

####################################################################################################################################################################################
############################################################ APPLICANT #############################################################################################################
####################################################################################################################################################################################




@main.route('/applicant_home/<int:hr_id>/<int:interview_parameter_id>', methods=['GET', 'POST'])
def applicant_home(hr_id, interview_parameter_id):
    hr = HR.query.get_or_404(hr_id)
    interview_parameter = InterviewParameter.query.get_or_404(interview_parameter_id)
    interview_id = interview_parameter.interview_id
    interview = Interview.query.get_or_404(interview_id)
    duration = interview_parameter.duration
    company = Company.query.get_or_404(hr.company_id)
    company_name = company.name
    
    error_message = None

    if request.method == 'POST':
        # Fetch form data directly from POST
        name = request.form.get('name')
        surname = request.form.get('surname')
        email = request.form.get('email')

        # Server-side validation
        if not name or not surname or not email:
            error_message = "All fields are required."
            return render_template(
                'applicant/applicant_home.html', 
                interview_parameter_id=interview_parameter_id,
                interview = interview, 
                hr_id = hr_id,
                role=interview_parameter.role,
                subrole = interview_parameter.subrole, 
                industry=interview_parameter.industry, 
                hr_email=hr.email,
                duration=duration,
                company_name = company_name,
                error_message=error_message
            )

        # Create a new applicant
        new_applicant = Applicant(name=name, surname=surname, email_address=email)
        db.session.add(new_applicant)
        db.session.commit()

        # Redirect directly to start_chat
        return redirect(url_for('main.start_chat', hr_id=hr_id, interview_parameter_id=interview_parameter_id, interview_id=interview_id, applicant_id=new_applicant.id))
    
    return render_template(
        'applicant/applicant_home.html', 
        interview_parameter_id=interview_parameter_id,
        interview = interview, 
        hr_id = hr_id,
        role=interview_parameter.role,
        subrole = interview_parameter.subrole, 
        industry=interview_parameter.industry, 
        hr_email=hr.email,
        duration=duration,
        company_name = company_name,
        error_message=error_message  # Pass the error message to the template
    )




@main.route('/start/<int:hr_id>/<int:interview_parameter_id>/<int:interview_id>/<int:applicant_id>', methods=['GET', 'POST'])
def start_chat(hr_id, interview_parameter_id, interview_id, applicant_id):
    # Retrieve existing session for the applicant to prevent creating duplicate sessions
    existing_session = Session.query.filter_by(applicant_id=applicant_id, interview_parameter_id=interview_parameter_id).first()

    # If a session exists, redirect to the existing session's chat
    if existing_session:
        return redirect(url_for('main.chat', 
                                hr_id=hr_id, 
                                interview_id=interview_id, 
                                interview_parameter_id=interview_parameter_id, 
                                session_id=existing_session.id, 
                                applicant_name=existing_session.applicant.name, 
                                applicant_id=existing_session.applicant_id))
    
    # Retrieve data
    interview_parameter = InterviewParameter.query.get_or_404(interview_parameter_id)
    applicant = Applicant.query.get_or_404(applicant_id)
    hr = HR.query.get_or_404(hr_id)

    company = Company.query.get_or_404(hr.company_id)

    company_name = company.name

    # Create thread
    thread_id, assistant_id, assistant_response = create_openai_thread(
        interview_parameter.language,
        interview_parameter.role,
        interview_parameter.subrole,
        interview_parameter.industry,
        interview_parameter.situation,
        applicant.name,
        applicant.surname,
        company_name
    )
    
    # Create and save a new session
    new_session = Session(interview_parameter_id=interview_parameter_id,
                        applicant_id=applicant_id,
                        remaining_time = 60*int(interview_parameter.duration), 
                        thread_id = thread_id, 
                        assistant_id = assistant_id,
                        finished=False)
    
    db.session.add(new_session)
    db.session.commit()

    # Generate the voice for the assistant response using AWS Polly
    
    audio_file_path = generate_voice(assistant_response, interview_parameter.language, f'assistant_response_{new_session.id}_{int(time.time())}.mp3')

    print(f"Audio file path generated: {audio_file_path}")

    # Create and save the question
    question = Question(
        content=assistant_response, 
        session_id=new_session.id,
        audio_file_path=audio_file_path  # Save the audio file path
    )
    db.session.add(question)
    db.session.commit()


    return redirect(url_for('main.chat', 
                            hr_id=hr_id, 
                            interview_id=interview_id, 
                            interview_parameter_id=interview_parameter_id, 
                            session_id=new_session.id, 
                            applicant_name=applicant.name, 
                            applicant_id=applicant.id))



@main.route('/chat/<int:hr_id>/<int:interview_id>/<int:interview_parameter_id>/<int:session_id>/<int:applicant_id>', methods=['GET', 'POST'])
def chat(hr_id, interview_id, interview_parameter_id, session_id, applicant_id):
    
    # Retrieve data
    hr = HR.query.get_or_404(hr_id)
    company = Company.query.get_or_404(hr.company_id)

    interview_parameter = InterviewParameter.query.get_or_404(interview_parameter_id)
    interview = Interview.query.get_or_404(interview_id)
    current_session = Session.query.get_or_404(session_id)
    applicant = Applicant.query.get_or_404(applicant_id)
    questions = Question.query.filter_by(session_id=session_id).all()
    answers = Answer.query.filter_by(session_id=session_id).all()

    thread_id = current_session.thread_id
    assistant_id = current_session.assistant_id
    
    applicant_name = applicant.name
    applicant_email = applicant.email_address
    applicant_surname = applicant.surname

    max_questions = interview_parameter.max_questions
    thank_you_message = get_thank_you_message(applicant.name)
    timestamp = int(time.time())

    # If POST
    if request.method == 'POST':
        user_input = request.form['answer']
        question_id = request.form['question_id'] # ALWAYS THE SAME QUESTION ID
        remaining_time = int(request.form['remaining_time'])
        current_session.remaining_time = remaining_time
        db.session.commit()

        if not thread_id or not assistant_id:
            return redirect(url_for('main.chat', 
                                    hr_id=hr_id, 
                                    interview_id=interview_id, 
                                    interview_parameter_id=interview_parameter_id, 
                                    session_id=session_id,
                                    applicant_id=applicant_id))
        else:
            answer = Answer(content=user_input, question_id=question_id, session_id=session_id)
            db.session.add(answer)
            db.session.commit()

        

        if remaining_time <= 0:
            current_session.finished = True
            db.session.commit()
            hr_email = hr.email
            hr_link = get_url('main.home', hr_id=hr_id)
            msg = Message('Interview Finished',
                          sender='noreply@tunz.ai',
                          recipients=[hr_email])
            msg.body = f'The interview of {applicant_name} {applicant_surname} (email: {applicant_email}) has finished. Click the following link to view the result: {hr_link}'
            mail.send(msg)

        else:
            assistant_response = get_openai_thread_response(thread_id, assistant_id, user_input)
            # Generate the voice for the assistant response
            audio_file_path = generate_voice(assistant_response, interview_parameter.language, f'assistant_response_{session_id}_{timestamp}.mp3')
            print(f"Audio file path generated: {audio_file_path}")
            
            # Save the new question and its associated audio file path
            question = Question(
                content=assistant_response, 
                session_id=session_id,
                audio_file_path=audio_file_path
            )
            db.session.add(question)
            db.session.commit()

        # STILL NEED TO BE ENHANCED: WHEN THE SESSION IS FINISHED? NOT POSSIBLE TO COME BACK

        return redirect(url_for('main.chat', 
                            hr_id=hr_id, 
                            interview_id=interview_id, 
                            interview_parameter_id=interview_parameter_id, 
                            session_id=session_id, 
                            applicant_name=applicant_name, 
                            applicant_id=applicant.id))
        
    remaining_time = current_session.remaining_time

    return render_template('applicant/chat.html',
                           interview_parameter = interview_parameter,
                           interview = interview,
                           company = company,
                           hr =hr,
                           questions=questions,
                           hr_id=hr_id,
                           answers=answers,
                           max_questions=max_questions,
                           thank_you_message=thank_you_message,
                           applicant_name=applicant_name,
                           duration=remaining_time,
                           session_id=session_id,
                           is_finished=current_session.finished,
                           interview_id=interview_id,
                           interview_parameter_id=interview_parameter_id,
                           applicant_id=applicant_id,
                           applicant = applicant,
                           timestamp = timestamp)



@main.route('/finish_interview/<int:hr_id>/<int:interview_id>/<int:interview_parameter_id>/<int:session_id>/<int:applicant_id>', methods=['GET'])
def finish_chat(hr_id, interview_id, interview_parameter_id, session_id, applicant_id):
    #db.session.commit()
    current_session = Session.query.get_or_404(session_id)
    current_session.finished = True
    db.session.commit()
    interview = Interview.query.get_or_404(interview_id)
    interview_parameter = InterviewParameter.query.get_or_404(interview_parameter_id)
    hr = HR.query.get_or_404(hr_id)
    hr_email =  hr.email
    applicant = Applicant.query.get_or_404(applicant_id)
    applicant_name = applicant.name
    applicant_email = applicant.email_address
    applicant_surname = applicant.surname

    answers = Answer.query.filter_by(session_id=session_id).all()

    conversation = get_interview_conversation(session_id)
    
    score_interview = create_scoring_thread(interview_parameter.language, 
                                                                     interview_parameter.role, 
                                                                     interview_parameter.subrole,
                                                                     interview_parameter.industry, 
                                                                     interview_parameter.situation, 
                                                                     conversation)
    
    # Convert the dictionary to a JSON string before saving to the database
    score_interview_str = json.loads(score_interview)  
    
    result = Result(score_type = 'applicant_score', session_id = session_id, score_interview = score_interview_str)
    db.session.add(result)
    db.session.commit()

    hr_link = get_url('main.session_details',
                      hr_id = hr_id, session_id = session_id)
    msg = Message('Interview Finished',
                  sender='noreply@tunz.ai',
                  recipients=[hr_email])
    msg.body = f'The interview of {applicant_name} {applicant_surname} (email: {applicant_email}) for the {interview.name} position has finished. You can find the interview details by clicking on the following link: {hr_link}. On your dashboard, you will also be able to compare this interview with the other applicants.'
    mail.send(msg)
    return redirect(url_for('main.applicant_review',  
                            hr_id = hr_id, 
                            interview_id=interview_id, 
                            interview_parameter_id=interview_parameter_id, 
                            session_id=session_id, 
                            applicant_id = applicant_id))


@main.route('/applicant_review/<int:hr_id>/<int:interview_id>/<int:interview_parameter_id>/<int:session_id>/<int:applicant_id>', methods=['GET', 'POST'])
def applicant_review(hr_id, interview_id, interview_parameter_id, session_id, applicant_id):
    applicant = Applicant.query.get_or_404(applicant_id)
    hr = HR.query.get_or_404(hr_id)
    company = Company.query.get_or_404(hr.company_id)
    questions = [
        "How was the user experience with the AI interface?",
        "How fluid was the conversation?",
        "How pertinent were the questions?",
    ]

    if request.method == 'POST':
        # Retrieve the submitted ratings and comment
        comment = request.form.get('comment')
        ratings = [int(request.form.get(f'rating_{i}', 0)) for i in range(len(questions))]

        # Save the review to the database
        review = Review(session_id=session_id, comment=comment)
        db.session.add(review)
        db.session.commit()

        # Save the ratings for each question
        for idx, rating in enumerate(ratings):
            question = ReviewQuestion(
                text=questions[idx],
                rating=rating,
                review_id=review.id
            )
            db.session.add(question)

        db.session.commit()

        flash('Thank you for your feedback!', 'success')
        return redirect(url_for('main.applicant_result',
                                hr_id=hr_id,
                                interview_id=interview_id,
                                interview_parameter_id=interview_parameter_id,
                                session_id=session_id,
                                applicant_id=applicant_id))
    
    return render_template('applicant/applicant_review.html',
                           applicant = applicant,
                           company = company,
                           questions=questions,
                           hr_id=hr_id,
                           interview_id=interview_id,
                           interview_parameter_id=interview_parameter_id,
                           session_id=session_id,
                           applicant_id=applicant_id,
                           enumerate=enumerate)



@main.route('/applicant_result/<int:hr_id>/<int:interview_id>/<int:interview_parameter_id>/<int:session_id>/<int:applicant_id>', methods=['GET'])
def applicant_result(hr_id, interview_id, interview_parameter_id, session_id, applicant_id):
    hr = HR.query.get_or_404(hr_id)
    company = Company.query.get_or_404(hr.company_id)
    current_session_id = session_id
    interview = Interview.query.get_or_404(interview_id)
    interview_parameter = InterviewParameter.query.get_or_404(interview_parameter_id)
    if not current_session_id:
        return redirect(url_for('main.home'))
    score = Result.query.filter_by(session_id=session_id).first()  # Implement this function based on your grading logic
    applicant_feedback = score.score_interview['applicant_feedback']


    applicant = Applicant.query.get_or_404(applicant_id)
    applicant_name = applicant.name
    applicant_email = applicant.email_address
    applicant_surname = applicant.surname

    return render_template('applicant/applicant_result.html',
                            score=score, 
                            applicant_feedback = applicant_feedback,
                            applicant_email=applicant_email, 
                            applicant_name=applicant_name, 
                            applicant_surname=applicant_surname, 
                            applicant_id = applicant_id,
                            company = company,
                            interview = interview,
                            enumerate=enumerate)








