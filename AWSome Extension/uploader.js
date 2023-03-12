import AWS from 'aws-sdk'
import * as fs from 'fs';

async function uploader(videoTitle) {
    const s3 = new AWS.S3({
        accessKeyId: 'AKIARHZOHOJVNZJSTJVU',
        secretAccessKey: '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',
    })
    
    const uploadedImage = await s3.upload({
        Bucket: 'teamawsomebucket',
        Key: 'lecture.mp4',
        Body: fs.createReadStream('lecture.mp4'),
    }).promise()

}

export default uploader;


uploader('sdas')
//arn:aws:s3:ap-southeast-1:085459432042:accesspoint/*