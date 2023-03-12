
chrome.tabs.query({
    'active':true, 
    'lastFocusedWindow': true
},
(tabs) => {
   var url = tabs[0].url
    var message = {
        'url': url,
        'quality': "highest",
        'filename': "lecture",
        'format' : "mp4"
    };
    chrome.runtime.sendMessage(message);
})

//await uploader('lecture.mp4')