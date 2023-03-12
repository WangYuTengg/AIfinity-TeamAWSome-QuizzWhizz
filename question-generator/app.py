import streamlit as st
import pandas as pd
import json
import boto3
import cv2
import numpy as np
import time
from moviepy.editor import *
from fuzzywuzzy import fuzz
from pipelines import pipeline
import random

AWS_ACCESS_KEY_ID="AKIARHZOHOJVNZJSTJVU"
AWS_SECRET_ACCESS_KEY="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"
AWS_DEFAULT_REGION = "ap-southeast-1"
BUCKET_NAME = 'teamawsome-testbucket'
################################################################################################################################

title = st.container()
with title:
    st.title("Welcome to Quiz Whizz!")
    st.write("Convert your lecture videos to bite-sized questions!")
    st.write("----")
    
    # video upload
    uploaded_file = st.file_uploader("Upload video here:", type=["mp4"])
    if uploaded_file is not None:
        # save video to disk locally
        i = random.randint(0,9999)
        video_file_name = "lecture"+ str(i)+ ".mp4"
        with open(video_file_name, "wb") as f:
            f.write(uploaded_file.read())
        
        # display video on app
        st.header("Video Uploaded:")
        st.video(uploaded_file)

        # upload video to s3
        s3client = boto3.client("s3",
                      aws_access_key_id = AWS_ACCESS_KEY_ID,
                      aws_secret_access_key = AWS_SECRET_ACCESS_KEY,
                      region_name = AWS_DEFAULT_REGION)
        s3client.upload_file(video_file_name, BUCKET_NAME, video_file_name)

    else:
        st.write("Upload a video")
    st.write("---")

################################################################################################################################

# text_audio extraction
def mainExtraction(video_file, bucket_name):
    st.header("Audio transcription extraction process: ")
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
    
    # set audio input file bucket
    # s3client.download_file(bucket_name, video_file, video_file)
    
    # Load the mp4 file
    video = VideoFileClip(video_file)
    
    # Extract audio from video
    video.audio.write_audiofile(video_file+".mp3")
    st.write("Extracting audio from video...")

    #check files in audio folder
    audio_list = []
    for audio in os.listdir():
        if '.mp3' in audio:
            print("Sanity check 1:", audio)
            audio_list.append(audio)

    audio_data = pd.DataFrame({'audio_name': audio_list})
    audio_data.head()
    
    #upload audio files to s3
    for audio_file in audio_data.audio_name.values:
        print("Sanity check 2:", audio_file)
        s3client.upload_file(audio_file, bucket_name,  audio_file)
        st.write("Uploading audio files to S3...")

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
                'MaxSpeakerLabels': 2,
            },
            )
            if wait_process:
                while True:
                    status = transcribeclient.get_transcription_job(TranscriptionJobName = job_name)
                    if status['TranscriptionJob']['TranscriptionJobStatus'] in ['COMPLETED','FAILED']:
                        break
                    print("Not ready yet")
                    st.write("Transcription in progress...")
                    time.sleep(20)

                print("Transcription Finished")
                st.write("Audio transcription completed")
                return status
        except:
            print("transcription job for this file already done")
    
    # start transcription on audio file
    for index, row in audio_data.iterrows():
        print(f'{row.audio_name}', row.url)
        start_transcription(bucket_name, f"{row.audio_name}", row.url, wait_process=True)
        # get json of transcription in s3
        st.write("Downloading json file of transcription from S3")
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

    # Display audio transcription
    st.subheader("Audio transcription text obtained: ")
    st.write(audio_transcription_text)
    print(audio_transcription_text)

# text_video extraction
def mainExtraction2(video_file):
    st.header("Visual text extraction process: ")
    cam = cv2.VideoCapture(video_file)
    
    # Set the desired width and height of the resized frames
    width = 1100
    height = 900

    # should do this in s3 instead of locally
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
    
    st.write("Extracting video frames...")
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
                # sharpen the images
                sharpened = cv2.filter2D(resized, -1, sharpen_filter)
    
                # writing the extracted images
                cv2.imwrite(name, sharpened)
      
                # increasing counter so that it will
                # show how many frames are created
                currentframe += 1
                time_elapsed = current_time
        else:
            break

    st.write("Sharpening and resizing frames...")
    # Release all space and windows once done
    cam.release()
    # cv2.destroyAllWindows
    
    # extraction of text from video frames 
    st.write("Extracting text from video frames...")
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
    st.write("Cleaning up text...")
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
    st.write("Combining text...")
    video_transcription_text = ""
    for s in unique_list:
        if s == "" or s == " " or percentage_numerical(s) >= 0.40:
            continue
        video_transcription_text += s
        video_transcription_text += "\n\n"

    # display extracted text
    st.subheader("Visual Text Extracted: ")
    st.write(video_transcription_text)
    return video_transcription_text

if (uploaded_file):
    mainExtraction(video_file_name, BUCKET_NAME)
    st.write("---")
    # Opening JSON file
    f = open(video_file_name + "_uniqueJob.json")    
    data = json.load(f)
    text_audio = data['results']['transcripts'][0].get('transcript')
    f.close()
    text_video = mainExtraction2(video_file_name)
    st.write("---")

# Generate questions
fulltext = text_audio + text_video
if fulltext:
    with st.spinner(text="Generating questions..."):
        time.sleep(10)
        
    st.header("Questions generated: ")
    nlp = pipeline("e2e-qg")
    review_questions = nlp(text_audio)
    review_questions.extend(nlp(text_video))
    # review_questions = ["What type of wind wind is caused by air moving from higher pressure to an area of lower air pressure?",
    #                     "Why does air move from vold to warm?",
    #                     "Why does air want to leave the balloon?",
    #                     "What is a great sea breeze during the day",
    #                     "What is Anenometer and Wind Vane?",
    #                     "What is created during the day because ground heats up more quickly than water",
    #                     "What is the Coriolis Effect Wind Chill Wind Chill?",
    #                     ]

    # display questions
    i = 1
    for question in review_questions:
        st.write("Q" + str(i) + ")", question)
        i += 1
