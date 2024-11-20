import os
import boto3
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.getenv('AWS_REGION', 'eu-west-3')  # Paris

# Initialize the Transcribe client
transcribe_client = boto3.client(
    'transcribe',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

"""Transcribes the audio from a media file and applies any additional Request Parameters you choose to include in your request.
To make a StartTranscriptionJob request, you must first upload your media file into an Amazon S3 bucket; 
you can then specify the Amazon S3 location of the file using the Media parameter.
See: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/transcribe/client/start_transcription_job.html """

def transcribe_audio(audio_file_uri, job_name, language_code='en-US'):
    """
    Transcribe an audio file using AWS Transcribe.
    :param audio_file_uri: S3 URI of the audio file.
    :param job_name: A unique job name for the transcription.
    :param language_code: Language code for transcription.
    :return: The transcription result (text).
    """
    response = transcribe_client.start_transcription_job(
        TranscriptionJobName=job_name,
        Media={'MediaFileUri': audio_file_uri},
        MediaFormat='mp3',  # Adjust this based on your audio format
        LanguageCode=language_code
    )

    return response


"""To view the status of the specified transcription job, check the TranscriptionJobStatus field. 
If the status is COMPLETED, the job is finished. You can find the results at the location specified in TranscriptFileUri. 
If the status is FAILED, FailureReason provides details on why your transcription job failed.
If you enabled content redaction, the redacted transcript can be found at the location specified in RedactedTranscriptFileUri."""

def get_transcription_result(job_name):
    """
    Get the transcription result for a given job.
    :param job_name: The transcription job name.
    :return: Transcription text if available.
    """
    result = transcribe_client.get_transcription_job(TranscriptionJobName=job_name)
    if result['TranscriptionJob']['TranscriptionJobStatus'] == 'COMPLETED':
        transcription_url = result['TranscriptionJob']['Transcript']['TranscriptFileUri']
        transcription_text = fetch_transcription_from_url(transcription_url)
        return transcription_text
    else:
        return None
    


def fetch_transcription_from_url(url):
    """
    Fetches the transcription result from the AWS Transcribe result URL.
    :param url: The URL where the transcription JSON is located.
    :return: The transcription text.
    """
    response = requests.get(url)
    
    if response.status_code == 200:
        transcription_data = response.json()
        transcription_text = transcription_data['results']['transcripts'][0]['transcript']
        return transcription_text
    else:
        raise Exception(f"Failed to fetch transcription from URL: {url}. HTTP Status: {response.status_code}")