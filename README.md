# AWS AIfinity Hackathon 2023 - Project: QuizzWhizz (by Team AWSome)
<img width="1438" src="https://github.com/WangYuTengg/AIfinity-TeamAWSome-QuizzWhizz/blob/master/img1.PNG?raw=true">

## Hackathon Theme
AI as Productivity Promoter As the emergence of stronger AI models (such as ChatGPT), intense human labour has a higher chance to be replace by AI. In an era of such trend, human beings might need to adapt to new paradigms of production with the help of AI. Try to give your proposal for such new paradigms, and build prototypes with resources provided.

###  Inspiration:
As students, we face many challenges in our pursuit of academics. We felt that lectures can be very long and we tend to lose our focus. Thus, having a quiz available for each lecture video can help us be more attentive and learn better. We were inspired to build a project that can help ourselves and fellow students become more productive and efficient academically.

## 💡 What it does
Our project firstly enables users to conveniently download videos of their choice through a chrome extension that we built. Secondly, videos can be uploaded onto our quiz generation platform to retrieve a series of questions that were generated from the input video.

## 💻 How we built it
- Frontend/UI - Streamlit 
- Transcription - Amazon Transcribe 
- Text extraction from video - Amazon Textract 
- Question Generator - External Library using Transformers 
- Chrome Extension - Express.JS, JavaScript 
- Data cloud storage - Amazon S3 
- Machine Learning and Data processing - Amazon Sagemaker, OpenCV

## 😰 Challenges we ran into
* Integration hell and unsuccessfully deploying our Sagemaker notebook as a lambda function on AWS Lambda together with API Gateway.
* Trying to get a higher quality of questions generated, there were a lot of incoherent questions with grammatical and spelling errors initially.
* The overwhelming number of available AWS services and APIs and the complexity of using them successfully.

## 🥇 Accomplishments that we're proud of
* We are extremely proud of building and deploying a functional AI product in less than 2 days despite our unfamiliarity with AWS and its tools.
* We are also proud of achieving decent quality of questions generated
* We are lastly proud of being able to use a combination of 3 fields of AI: CV, NLP and speech processing.

## 🔑 What we learned
* We learnt how to navigate the AWS Sagemaker MLOPs environment
* We learnt how to make a chrome extension with a decent utility
* We learnt how to use and deploy AWS deep learning tools such as Textract and Amazon Transcribe
* We learn how to integrate everything together into a user-friendly AI solution

## 👀 What's next for QuizzWizz 
Deploy application on a cloud server
Increase accuracy of transcription, text extraction and improve quality of question generated
Increase support for other URLs ( other than youtube .mp4 videos)
Increase support for other file types, e.g text documents

## ✍🏻 Contributors
* Mary Soh [@marysoh](https://github.com/marysoh)
* Jayden Yeo [@MomPansy](https://github.com/MomPansy)
* Wang Yu Teng [@WangYuTengg](https://github.com/WangYuTengg)
* Andre Pang
