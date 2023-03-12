import streamlit as st
import pandas as pd
import json
import boto3
import cv2
import numpy as np
import time
from botocore.exceptions import ClientError
from moviepy.editor import *
from fuzzywuzzy import fuzz
from pipelines import pipeline
import tempfile

AWS_ACCESS_KEY_ID="xxx"
AWS_SECRET_ACCESS_KEY="xxx"
AWS_DEFAULT_REGION = "xxx"
BUCKET_NAME = 'teamawsome-testbucket'
################################################################################################################################

title = st.container()
with title:
    st.title("Welcome to AI Question Generator")
    st.write("----")
    uploaded_file = st.file_uploader("Upload file")
    if uploaded_file:
        st.header("Video Uploaded:")
        st.video(uploaded_file)
        s3client = boto3.client("s3",
                      aws_access_key_id = AWS_ACCESS_KEY_ID,
                      aws_secret_access_key = AWS_SECRET_ACCESS_KEY,
                      region_name = AWS_DEFAULT_REGION)
        s3client.upload_file(uploaded_file.name, BUCKET_NAME, uploaded_file.name)
    else:
        st.write("Upload a file")
    st.write("----")

################################################################################################################################

# text_audio extraction
def mainExtraction(video_file, bucket):
    # some default values
    bucket_name = bucket
    videofile = video_file
    
    # define the aws services
    transcribeclient = boto3.client("transcribe",
                      aws_access_key_id = AWS_ACCESS_KEY_ID,
                      aws_secret_access_key = AWS_SECRET_ACCESS_KEY,
                      region_name = AWS_DEFAULT_REGION)
    
    s3client = boto3.client("s3",
                      aws_access_key_id = AWS_ACCESS_KEY_ID,
                      aws_secret_access_key = AWS_SECRET_ACCESS_KEY,
                      region_name = AWS_DEFAULT_REGION)
    
    s3 = boto3.resource('s3',
                    aws_access_key_id = AWS_ACCESS_KEY_ID,
                    aws_secret_access_key = AWS_SECRET_ACCESS_KEY,
                    region_name = AWS_DEFAULT_REGION
                    )
    
    #set audio input file bucket
    s3client.download_file(bucket_name, videofile, videofile)
    
    # Load the mp4 file
    video = VideoFileClip(video_file)
    
    # Extract audio from video
    video.audio.write_audiofile(videofile+".mp3")

    #check files in audio folder
    audio_list = []
    for audio in os.listdir():
        if '.mp3' in audio:
            print("Sanity check:", audio)
            audio_list.append(audio)

    audio_data = pd.DataFrame({'audio_name': audio_list})
    audio_data.head()
    
    #upload audio files to s3
    for audio_file in audio_data.audio_name.values:
        print("Sanity check 2:", audio_file)
        s3client.upload_file(audio_file, bucket_name,  audio_file)
    
    #define urls on bucket
    for index,row in audio_data.iterrows():
        print("1", index)
        print("1", row)
        bucket_location = s3client.get_bucket_location(Bucket=bucket_name)
        object_url = f"s3://{bucket_name}/{row['audio_name']}"
        audio_data.at[index,'url'] = object_url
        print("object URL:",object_url)
    
    #helper function for transcribing
    def start_transcription(bucket, job_name, file_url, wait_process=True):
        job_name = job_name.replace(' ', '_')
        job_name = job_name.replace('.mp3', '_uniqueJob')
        try:
            response = transcribeclient.start_transcription_job(
            TranscriptionJobName=job_name,
            LanguageCode='en-US', 
            MediaFormat='mp3',
            Media={
                'MediaFileUri': file_url,
            },
            OutputBucketName= bucket,
            Settings={
                'ShowSpeakerLabels': True,
                'MaxSpeakerLabels': 2 },
            )
            if wait_process:
                while True:
                    status = transcribeclient.get_transcription_job(TranscriptionJobName = job_name)
                    if status['TranscriptionJob']['TranscriptionJobStatus'] in ['COMPLETED','FAILED']:
                        break
                    print("Not ready yet")
                    time.sleep(20)

                print("Transcription Finished")
                return status
        except:
            print("transcription job for this file already done")
    
    # start transcription on audio file
    for index, row in audio_data.iterrows():
        print(f'{row.audio_name}', row.url)
        start_transcription(bucket_name, f"{row.audio_name}", row.url, wait_process=True)
        # get json of transcription in s3
        audio_data.at[index, 'transcription_url'] = f"https://{bucket_name}.s3.amazonaws.com/{row.audio_name}.json"
        audio_data.at[index, 'json_transcription'] = f"{row.audio_name}.json"

    # download .json files from s3
    my_bucket = s3.Bucket(bucket_name)
    for s3_object in my_bucket.objects.all():
        path, filename = os.path.split(s3_object.key)
        if filename.split('.')[-1] in ['json']:
            my_bucket.download_file(s3_object.key, filename)
    
    # Opening JSON file
    f = open(video_file + "_uniqueJob.json")    
    data = json.load(f)
    audio_transcription_text = data['results']['transcripts'][0].get('transcript')
    # Closing file
    f.close()
    print(audio_transcription_text)

# text_video extraction
def mainExtraction2(video_file):
    cam = cv2.VideoCapture(video_file)
    
    # Set the desired width and height of the resized frames
    width = 1000
    height = 800
    
    try:
        # creating a folder named data
        if not os.path.exists('video-frames-'+video_file):
            os.makedirs('video-frames-'+video_file)
      
    # if not created then raise error
    except OSError:
        print ('Error: Creating directory of data')
      
    # frame
    currentframe = 0
    time_elapsed = 0 # elapsed time in seconds
      
    while(True):
          
        # reading from frame
        ret,frame = cam.read()
      
        if ret:
            # get current time in seconds
            current_time = cam.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
            
            # check if elapsed time is greater than 10 seconds
            if current_time >= time_elapsed + 10.0:
                
                # if video is still left continue creating images
                name = './video-frames-'+video_file+'/frame' + str(currentframe) + '.png'
                resized = cv2.resize(frame, (width, height))
                sharpen_filter=np.array([[-1,-1,-1],
                     [-1,9,-1],
                    [-1,-1,-1]])
                # sharpen the image to make writing more legible
                sharpened = cv2.filter2D(resized, -1, sharpen_filter)
    
                # writing the extracted images
                cv2.imwrite(name, sharpened)
      
                # increasing counter so that it will
                # show how many frames are created
                currentframe += 1
                time_elapsed = current_time
        else:
            break
    
    # Release all space and windows once done
    cam.release()
    # cv2.destroyAllWindows
    
    # extraction of text from video frames 
    fulltext_set = set()
    dir = 'video-frames-'+video_file
    client = boto3.client("textract",
                      aws_access_key_id = AWS_ACCESS_KEY_ID,
                      aws_secret_access_key = AWS_SECRET_ACCESS_KEY,
                      region_name = AWS_DEFAULT_REGION)    
    
    for file in os.listdir(dir):
        try:
            fullpath = os.path.join(dir,file)
            with open(fullpath, 'rb') as file:
                img_test = file.read()
                bytes_test = bytearray(img_test)
            response = client.analyze_document(Document={'Bytes': bytes_test},FeatureTypes = ['TABLES'])
            # print(response)
    
            blocks = response['Blocks']
            text = ""
            for block in blocks:
                if (block['BlockType'] == 'WORD'):
                    text += block['Text'] + ' '
        
            # get rid of exact duplicates
            if text in fulltext_set:
                continue
            else:
                fulltext_set.add(text)
        except:
            continue
    
    print("Extraction done")
    
    # get rid of near-duplicates due to inaccurate text extraction 
    unique_list = []
    fulltext_list = list(fulltext_set)
    
    for text in fulltext_list:
        if not any(fuzz.ratio(text, unique_text) >= 70 for unique_text in unique_list):
            unique_list.append(text)
    
    # helper function to check for percentage of number characters in a string
    def percentage_numerical(inputstring):
        n = 0
        for char in inputstring:
            if char.isdigit():
                n += 1
        return float(n / len(inputstring))
    
    # combine into one text string
    video_transcription_text = ""
    for s in unique_list:
        if s == "" or s == " " or percentage_numerical(s) >= 0.40:
            continue
        video_transcription_text += s
        video_transcription_text += "\n\n"
    return video_transcription_text

if (uploaded_file):
    video_file = uploaded_file.name
    mainExtraction(video_file, BUCKET_NAME)
    # Opening JSON file
    f = open(video_file + "_uniqueJob.json")    
    data = json.load(f)
    text_audio = data['results']['transcripts'][0].get('transcript')
    # Closing JSON file
    f.close()
    text_video = mainExtraction2(video_file)

# run extracted text through pipeline to generate questions
questions = st.container()
with questions:
    nlp = pipeline("e2e-qg")
    review_questions = nlp(text_audio)
    review_questions.extend(nlp(text_video))
    st.header("Questions Generated from Video: ")
    i = 1
    for question in review_questions:
        st.write("Q" +str(i) + ")", question)
        i += 1
