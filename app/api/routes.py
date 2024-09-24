# Contains the routes related to API functionality.

import json
import math
from flask import Blueprint, jsonify, session
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from ..models import Question, Answer, Result, InterviewParameter, Session, Applicant, Review, ReviewQuestion, HR, Interview, Company, Admin
from .. import db
# API RETRIEVAL
api = Blueprint('api', __name__)


@api.route('/get_thread_id', methods=['GET'])
def get_thread_id():
    thread_id = session.get('thread_id')
    if not thread_id:
        return jsonify({'error': 'No thread_id found in session'}), 404

    return jsonify({'thread_id': thread_id}), 200


@api.route('/delete_interviews', methods=['DELETE'])
def delete_all_interviews():
    try:
        # Query all interviews
        interviews = Interview.query.all()
        
        # Delete each interview and cascade delete associated data
        for interview in interviews:
            db.session.delete(interview)
        
        db.session.commit()
        return jsonify({"msg": "All interviews and associated data have been deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "An error occurred while deleting interviews", "error": str(e)}), 500


@api.route('/interviews', methods=['GET'])
def get_all_interviews():
    try:
        # Query all interviews
        interviews = Interview.query.all()
        
        all_interviews = []
        for interview in interviews:
            interview_data = {
                'id': interview.id,
                'hr_id': interview.hr_id,
                'status': interview.status,
                'rules' : interview.rules,
                'name' : interview.name,
                'interview_parameters': [],
            }

            # Get interview parameters
            for param in interview.interview_parameters:
                param_data = {
                    'id': param.id,
                    'language': param.language,
                    'max_questions': param.max_questions,
                    'duration': param.duration,
                    'role': param.role,
                    'subrole': param.subrole,
                    'industry': param.industry,
                    # Add other fields from interview parameters if needed
                }
                interview_data['interview_parameters'].append(param_data)
            all_interviews.append(interview_data)
        
        return jsonify(all_interviews), 200
    except Exception as e:
        return jsonify({"msg": "An error occurred while fetching interviews", "error": str(e)}), 500
    


@api.route('/questions', methods=['GET'])
def get_questions():
    questions = Question.query.all()
    return jsonify([{
        'id': question.id,
        'content': question.content,
        'timestamp': question.timestamp,
        'session_id': question.session_id,
        'audio_file_path': question.audio_file_path  # Add the audio file path to the response
    } for question in questions])


@api.route('/delete_questions', methods=['DELETE'])
def delete_questions():
    try:
        questions = Question.query.all()
        for question in questions:
            db.session.delete(question)
        db.session.commit()
        return jsonify({"msg": "All questions have been deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "An error occurred while deleting questions", "error": str(e)}), 500


@api.route('/answers', methods=['GET'])
def get_answers():
    answers = Answer.query.all()
    return jsonify([{
        'id': answer.id,
        'content': answer.content,
        'question_id': answer.question_id,
        'timestamp': answer.timestamp,
        'session_id': answer.session_id
    } for answer in answers])


@api.route('/delete_answers', methods=['DELETE'])
def delete_all_answers():
    try:
        answers = Answer.query.all()
        for answer in answers:
            db.session.delete(answer)
        db.session.commit()
        return jsonify({"msg": "All answers have been deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "An error occurred while deleting answers", "error": str(e)}), 500




@api.route('/results', methods=['GET'])
def get_scores():
    results = Result.query.all()
    response = []

    for result in results:
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

            # Retrieve the criteria values
        criteria_value = [criteria_scores.get(key, 0) for key in criteria_keys]
        
        response.append({
            'id': result.id,
            'score_type': result.score_type,
            'session_id': result.session_id,
            'score_interview': score_interview,  # Ensure criteria_scores is properly formatted
            'criteria_value': criteria_value,
        })

    return jsonify(response)


@api.route('/delete_results', methods=['DELETE'])
def delete_scores():
    try:
        scores = Result.query.all()
        for score in scores:
            db.session.delete(score)
        db.session.commit()
        return jsonify({"msg": "All scores have been deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "An error occurred while deleting scores", "error": str(e)}), 500



@api.route('/interview_parameters', methods=['GET'])
def get_interview_parameters():
    interview_parameters = InterviewParameter.query.all()
    parameters_data = []

    for parameter in interview_parameters:
        situations = json.loads(parameter.situation) if parameter.situation else []
        ponderation = json.loads(parameter.ponderation) if parameter.ponderation else [[3, 3, 3, 3, 3, 3] for _ in range(len(situations))]

        parameters_data.append({
            'id': parameter.id,
            'language': parameter.language,
            'max_questions': parameter.max_questions,
            'duration': parameter.duration,
            'role': parameter.role,
            'subrole': parameter.subrole,
            'situations': situations,
            'industry': parameter.industry,
            'interview_id': parameter.interview_id,
            'ponderation': ponderation
        })

    return jsonify(parameters_data)



@api.route('/sessions', methods=['GET'])
def get_sessions():
    sessions = Session.query.all()
    return jsonify([{
        'remaining_time': session.remaining_time,
        'finished' : session.finished,
        'thread_id': session.thread_id,
        'assistant_id':session.assistant_id,
        'id': session.id,
        'start_time': session.start_time,
        'interview_parameter_id' : session.interview_parameter_id,
        'applicant_id' : session.applicant_id,
        'questions' : [{
            'id': question.id,
            'content': question.content,
            'timestamp': question.timestamp,
            'session_id': question.session_id
        } for question in session.questions],
        'answers' : [{
            'id': answer.id,
            'content': answer.content,
            'question_id': answer.question_id,
            'timestamp': answer.timestamp,
            'session_id': answer.session_id
        } for answer in session.answers],
        'results' : [{
            'id': result.id,
            'score_type': result.score_type,
            'score_result': result.score_result,
            'session_id': result.session_id
        } for result in session.results]
    } for session in sessions])


@api.route('/delete_sessions', methods=['DELETE'])
def delete_sessions():
    try:
        sessions = Session.query.all()
        for session in sessions:
            db.session.delete(session)
        db.session.commit()
        return jsonify({"msg": "All sessions have been deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "An error occurred while deleting sessions", "error": str(e)}), 500

@api.route('/delete_session/<int:session_id>', methods=['DELETE'])
def delete_session(session_id):
    try:
        session = Session.query.get(session_id)
        if not session:
            return jsonify({"msg": "Session not found"}), 404
        db.session.delete(session)
        db.session.commit()
        return jsonify({"msg": f"Session {session_id} has been deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "An error occurred while deleting the session", "error": str(e)}), 500
    

@api.route('/applicants', methods=['GET'])
def get_applicants():
    applicants = Applicant.query.all()
    return jsonify([{
        'id': applicant.id,
        'name': applicant.name,
        'surname': applicant.surname,
        'email_address': applicant.email_address,
    } for applicant in applicants])


@api.route('/delete_applicants', methods=['DELETE'])
def delete_all_applicants():
    try:
        applicants = Applicant.query.all()
        for applicant in applicants:
            db.session.delete(applicant)
        db.session.commit()
        return jsonify({"msg": "All applicants have been deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "An error occurred while deleting applicants", "error": str(e)}), 500



@api.route('/applicant_reviews', methods=['GET'])
def get_applicant_reviews():
    reviews = Review.query.all()
    all_reviews = []
    for review in reviews:
        review_data = {
            'review_id': review.id,
            'session_id': review.session_id,
            'comment': review.comment,
            'questions': []
        }
        review_questions = ReviewQuestion.query.filter_by(review_id=review.id).all()
        for question in review_questions:
            question_data = {
                'question_text': question.text,
                'rating': question.rating
            }
            review_data['questions'].append(question_data)
        all_reviews.append(review_data)
    return jsonify(all_reviews)


@api.route('/delete_applicant_reviews', methods=['DELETE'])
def delete_applicant_reviews():
    try:
        reviews = Review.query.all()
        for review in reviews:
            db.session.delete(review)
        db.session.commit()
        return jsonify({"msg": "All reviews have been deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "An error occurred while deleting reviews", "error": str(e)}), 500


@api.route('/mean_ratings_per_question', methods=['GET'])
def get_mean_ratings_per_question():
    from sqlalchemy import func
    questions = ReviewQuestion.query.with_entities(ReviewQuestion.text).distinct().all()
    question_ratings = {}
    for question in questions:
        avg_rating = db.session.query(func.avg(ReviewQuestion.rating)).filter(ReviewQuestion.text == question.text).scalar()
        question_ratings[question.text] = avg_rating
    return jsonify(question_ratings)



@api.route('/hrs', methods=['GET'])
#@jwt_required() # Ensure only authenticated user can acces them
def get_all_hrs():
    hrs = HR.query.all()
    all_hr_data = []
    for hr in hrs:
        hr_data = {
            'id': hr.id,
            'name': hr.name,
            'surname': hr.surname,
            'email': hr.email,
            'company_id': hr.company_id,
            'confirmed': hr.confirmed,
            'created_at': hr.created_at.strftime('%Y-%m-%d %H:%M:%S') if hr.created_at else None,
            'updated_at': hr.updated_at.strftime('%Y-%m-%d %H:%M:%S') if hr.updated_at else None
        }
        all_hr_data.append(hr_data)
    return jsonify(all_hr_data), 200


@api.route('/hr/<int:id>', methods=['GET'])
#@jwt_required() 
def get_hr(id):
    hr = HR.query.get_or_404(id)
    hr_data = {
        'id': hr.id,
        'name': hr.name,
        'surname': hr.surname,
        'email': hr.email,
        'company_id': hr.company_id,
        'confirmed': hr.confirmed,
        'created_at': hr.created_at.strftime('%Y-%m-%d %H:%M:%S') if hr.created_at else None,
        'updated_at': hr.updated_at.strftime('%Y-%m-%d %H:%M:%S') if hr.updated_at else None
    }
    return jsonify(hr_data), 200


@api.route('/hr/<int:id>', methods=['DELETE'])
#@jwt_required()
def delete_hr(id):
    hr = HR.query.get_or_404(id)
    db.session.delete(hr)
    db.session.commit()
    return jsonify({"msg": f"HR with id {id} has been deleted"}), 200


@api.route('/hrs', methods=['DELETE'])
#@jwt_required()
def delete_all_hrs():
    num_rows_deleted = db.session.query(HR).delete()
    db.session.commit()
    return jsonify({"msg": f"All HRs have been deleted, {num_rows_deleted} records deleted"}), 200



@api.route('/companies', methods=['GET'])
def get_companies():
    try:
        companies = Company.query.all()
        all_companies = []
        for company in companies:
            company_data = {
                'id': company.id,
                'name': company.name,
                'hrs': []
            }
            for hr in company.hr_managers:
                hr_data = {
                    'id': hr.id,
                    'email': hr.email,
                    'name': hr.name,
                    'surname': hr.surname,
                }
                company_data['hrs'].append(hr_data)
            all_companies.append(company_data)
        return jsonify(all_companies), 200
    except Exception as e:
        return jsonify({"msg": "An error occurred while fetching companies", "error": str(e)}), 500




@api.route('/delete_companies', methods=['DELETE'])
def delete_companies():
    try:
        companies = Company.query.all()
        for company in companies:
            db.session.delete(company)
        db.session.commit()
        return jsonify({"msg": "All companies have been deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "An error occurred while deleting companies", "error": str(e)}), 500
    

    #### ADMIN ####
@api.route('/admin/<int:admin_id>', methods=['GET'])
def get_admin(admin_id):
    admin = Admin.query.get(admin_id)
    if not admin:
        return jsonify({"msg": "Admin not found"}), 404
    
    admin_data = {
        "id": admin.id,
        "email": admin.email,
        "name": admin.name,
        "surname": admin.surname,
    }
    return jsonify(admin_data), 200
