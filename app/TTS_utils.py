import os
import boto3
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.getenv('AWS_REGION', 'eu-west-3')  # Paris


# Initialize the Polly client
polly_client = boto3.client('polly',
                            aws_access_key_id=AWS_ACCESS_KEY_ID,
                            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                            region_name=AWS_REGION)
def generate_voice(text, language, filename):
    """
    Generate speech using AWS Polly and save it as an MP3 file.
    
    :param text: The text to convert to speech.
    :param filename: The name of the file where the speech should be saved.
    :param language: The language of the interview
    :return: The path to the generated audio file (relative to the static directory).
    """
    
    # Define the voice ID mapping based on the language
    language_to_voice_id = {
        "English": "Matthew",
        "French": "Mathieu",
        "Spanish": "Miguel",
        "Dutch": "Ruben",
        "Italian": "Giorgio"
    }
    
    # Get the voice ID for the given language, default to English if not found
    voice_id = language_to_voice_id.get(language, "Matthew")
    
    # Wrap the text in SSML to adjust the speed
    ssml_text = f'<speak><prosody rate="102%">{text}</prosody></speak>'
    
    # Generate the audio using AWS Polly
    response = polly_client.synthesize_speech(
        TextType='ssml',  # Specify that we're using SSML
        Text=ssml_text,
        OutputFormat='mp3',
        VoiceId=voice_id
    )

    # Define audio directory relative to the 'static/' folder
    audio_directory = os.path.join('app','static', 'audio')
    if not os.path.exists(audio_directory):
        os.makedirs(audio_directory)

    # Save the file
    file_path = os.path.join(audio_directory, filename)
    with open(file_path, 'wb') as file:
        file.write(response['AudioStream'].read())

    # Return the relative path to the audio file
    return f'audio/{filename}'

