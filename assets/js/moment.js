// function checkIfLoggedIn() {
//   if(sessionStorage.getItem('username') == null){
//     window.location.href='';
//   } else {
//     //User already logged in
//     var userEntity = {};
//     userEntity = JSON.parse(sessionStorage.getItem('myUserEntity'));
//     ...
//     DoWhatever();
//   }
// }

function onLoad() {
    gapi.load('auth2', function () {
        gapi.auth2.init();
    });
}

function signOut() {
    var xhr = new XMLHttpRequest();
    xhr.open('POST', window.location.href, true);
    xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
    xhr.send("logout=true");
    console.log("fuck");
    var auth2 = gapi.auth2.getAuthInstance();
    auth2.signOut().then(function () {
    });
    window.location.href = "https://momentsync.net";
}

//video BEGIN

// var video;
var videowidth, videoheight;
//
// navigator.getUserMedia = (navigator.getUserMedia ||
//                           navigator.webkitGetUserMedia ||
//                           navigator.mozGetUserMedia ||
//                           navigator.msGetUserMedia ||
//                           navigator.oGetUserMedia );
//
//
// // Get access to the camera!
// if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
//     // Not adding `{ audio: true }` since we only want video now
//     navigator.mediaDevices.getUserMedia({video: true}).then(function (stream) {
//         //video.src = window.URL.createObjectURL(stream);
//         video.srcObject = stream;
//         videowidth = stream.getVideoTracks()[0].getSettings().width;
//         videoheight = stream.getVideoTracks()[0].getSettings().height;
//         video.play();
//     });
// }
var canvas = document.createElement('canvas');
var context = canvas.getContext('2d');

// Put event listeners into place
window.addEventListener("DOMContentLoaded", function () {
    // Grab elements, create settings, etc.
    var context = canvas.getContext('2d');
    var video = document.getElementById('video');
    var mediaConfig = {video: true};
    var errBack = function (e) {
        console.log('An error has occurred!', e)
    };

    // Put video listeners into place
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        navigator.mediaDevices.getUserMedia(mediaConfig).then(function (stream) {
            //video.src = window.URL.createObjectURL(stream);

            videowidth = stream.getVideoTracks()[0].getSettings().width;
            videoheight = stream.getVideoTracks()[0].getSettings().height;

            video.srcObject = stream;
            video.play();
        });
    }

    /* Legacy code below! */
    else if (navigator.getUserMedia) { // Standard
        navigator.getUserMedia(mediaConfig, function (stream) {
            video.src = stream;
            videowidth = stream.getVideoTracks()[0].getSettings().width;
            videoheight = stream.getVideoTracks()[0].getSettings().height;
            video.play();
        }, errBack);
    } else if (navigator.webkitGetUserMedia) { // WebKit-prefixed
        navigator.webkitGetUserMedia(mediaConfig, function (stream) {
            video.src = window.webkitURL.createObjectURL(stream);
            videowidth = stream.getVideoTracks()[0].getSettings().width;
            videoheight = stream.getVideoTracks()[0].getSettings().height;
            video.play();
        }, errBack);
    } else if (navigator.mozGetUserMedia) { // Mozilla-prefixed
        navigator.mozGetUserMedia(mediaConfig, function (stream) {
            video.src = window.URL.createObjectURL(stream);
            videowidth = stream.getVideoTracks()[0].getSettings().width;
            videoheight = stream.getVideoTracks()[0].getSettings().height;
            video.play();
        }, errBack);
    }

    // Trigger photo take
    document.getElementById('snap').addEventListener('click', function () {
        context.drawImage(video, 0, 0, 640, 480);
    });
}, false);


//video end

// Hide Header on on scroll down
var didScroll;
var lastScrollTop = 0;
var delta = 5;
var navbarHeight = $('header').outerHeight();

$(window).scroll(function (event) {
    didScroll = true;
});

setInterval(function () {
    if (didScroll) {
        hasScrolled();
        didScroll = false;
    }
}, 250);

function hasScrolled() {
    var st = $(this).scrollTop();

    // Make sure they scroll more than delta
    if (Math.abs(lastScrollTop - st) <= delta)
        return;

    // If they scrolled down and are past the navbar, add class .nav-up.
    // This is necessary so you never see what is "behind" the navbar.
    if (st > lastScrollTop && st > navbarHeight) {
        // Scroll Down
        $('header').removeClass('nav-down').addClass('nav-up');
    } else {
        // Scroll Up
        if (st + $(window).height() < $(document).height()) {
            $('header').removeClass('nav-up').addClass('nav-down');
        }
    }

    lastScrollTop = st;
}

function decodeBase64Image(dataString) {
    var matches = dataString.match(/^data:([A-Za-z-+\/]+);base64,(.+)$/);
    // response = {};

    // var image = new Image();
    // image.src = 'data:image/png;base64,'+matches[2];
    // response.data = new Buffer(matches[2], 'base64');
    // response.data = 'data:image/jpeg,base64,'+matches[2];
    return atob(matches[2]);

}


function dataURLtoFile(dataurl, filename) {
    var arr = dataurl.split(','), mime = arr[0].match(/:(.*?);/)[1],
        bstr = atob(arr[1]), n = bstr.length, u8arr = new Uint8Array(n);
    while (n--) {
        u8arr[n] = bstr.charCodeAt(n);
    }
    return new File([u8arr], filename, {type: mime});
}

var cameraDisplay;
// document.getElementById("cameraid").addEventListener("click", function () {
//     context.drawImage(video, 0, 0, canvas.width, canvas.height);
// });
$(function () {
    "use strict";

    $('.topnav-right a').click(function (event) {
        event.preventDefault();
        console.log("fucasdk");
        signOut();
    });

    $(".camera_button").click(function () {
        $('header').removeClass('nav-down').addClass('nav-up');
        $(".camera_button").fadeOut();
        $(".camera-view").fadeIn();

        let videoDisplay = $("video");

        canvas.width = videoDisplay.width();
        canvas.height = videoDisplay.height();

        // console.log(canvas.width);
        // console.log(canvas.height);

        // Trigger photo take
    });

    $(".popup img").click(function () {
        $('header').removeClass('nav-down').addClass('nav-up');
        $(".camera_button").fadeOut();
        var $src = $(this).attr("src");
        $(".show").fadeIn();
        $(".img-show img").attr("src", $src);
    });

    $(".closeButton, .overlay").click(function () {
        $(".show").fadeOut();
        $(".camera-view").fadeOut();
        $(".camera_button").fadeIn();
        $('header').removeClass('nav-up').addClass('nav-down');

    });

    $(".deleteButton").click(function () {
        $(".show").fadeOut();
        $('header').removeClass('nav-up').addClass('nav-down');
        $(".camera_button").fadeIn();


        var hashedNameR = $(".show .img-show img").attr("src");
        var name = hashedNameR.substr(hashedNameR.length - 32); // => "Tabs1"


        let response = {
            "type": "delete_moment",
            "value": name,
        };
        socket.send(JSON.stringify(response));
    });

    $(".shutter-button").click(function () {

        // var image = canvas.toDataURL("image/png").replace("image/png", "image/octet-stream");  // here is the most important part because if you dont replace you will get a DOM 18 exception.
        context.drawImage(video, 0, 0, canvas.width, canvas.height);
        var image = canvas.toDataURL("image/png");  // here is the most important part because if you dont replace you will get a DOM 18 exception.
        var filename = Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
        uploadBlobByStream(filename, dataURLtoFile(image));

    })

});


let MD5 = new Hashes.MD5;

function getBlobService() {
    blobUri = 'https://' + 'myhz.blob.core.windows.net';
    blobService = AzureStorage.Blob.createBlobServiceWithSas(blobUri, '?sv=2018-03-28&ss=b&srt=o&sp=c&se=2019-12-27T12:01:42Z&st=2018-12-27T04:01:42Z&spr=https&sig=D%2FN9Loq%2Fp60xBVbcK6BaUjttORWQNjM4g1a0chSXpA8%3D');

    return blobService;
}

function uploadBlobByStream(name, image) {

    // var files = document.getElementById('files').files;
    // if (!files.length) {
    //     alert('Please select a file!');
    //     return;
    // }
    // var file = files[0];

    var file = image;

    // console.log(file.type);
    // //
    var blobService = getBlobService();
    if (!blobService)
        return;
    //
    //
    // var btn = document.getElementById('upload-button');
    // btn.disabled = false;
    // btn.innerHTML = 'Uploading';
    //
    // // Make a smaller block size when uploading small blobs
    var blockSize = file.size > 1024 * 1024 * 32 ? 1024 * 1024 * 4 : 1024 * 512;
    var options = {
        storeBlobContentMD5: false,
        blockSize: blockSize,
        contentSettings: {
            contentType: "image/png"
        }
    };
    blobService.singleBlobPutThresholdInBytes = blockSize;


    hashedName = MD5.hex(name);

    var finishedOrError = false;
    var speedSummary = blobService.createBlockBlobFromBrowserFile("momentsync", hashedName, file, options, function (error, result, response) {
        // blobService.createReadStream()
        // var speedSummary = blobService.createBlockBlobFromText("momentsync", hashedName, file,  {'contentType': "image/png"}, function (error, result, response) {
        finishedOrError = true;
        if (error) {
            alert('Upload failed');
            console.log(error);
        } else {
            // setTimeout(function() { // Prevent alert from stopping UI progress update
            let response = {
                "type": "add_moment",
                "value": hashedName,
            };
            socket.send(JSON.stringify(response));

            // }, 1000);
        }
    });
}

let wsStart = 'ws://';
let loc = window.location;
if (loc.protocol === "https:") {
    wsStart = 'wss://';
}

//let is scoped for the closes enclosing block, var is for the nearest function block

let endpoint = wsStart + loc.host + loc.pathname;
let socket = new ReconnectingWebSocket(endpoint);
let username = sessionStorage.getItem('username');

socket.onmessage = function (e) {
    let json = JSON.parse(e.data);
    var momentContainer = document.getElementById("moments");
    if (json.type === "add_moment") {
        var moment = document.createElement("div");
        moment.id = json.value;
        moment.classList.add("column");
        moment.classList.add("is-one-quarter");
        moment.innerHTML = '<figure class="image is-5by4 popup"><img alt="Moment" src="https://cdn.momentsync.net/momentsync/' + json.value + '"</figure>';
        momentContainer.prepend(moment);

        $(".popup img").click(function () {
            $('header').removeClass('nav-down').addClass('nav-up');
            $(".camera_button").fadeOut();
            var $src = $(this).attr("src");
            $(".show").fadeIn();
            $(".img-show img").attr("src", $src);
        });

        $(".closeButton, .overlay").click(function () {
            $(".show").fadeOut();
            $(".camera-view").fadeOut();
            $(".camera_button").fadeIn();
            $('header').removeClass('nav-up').addClass('nav-down');
        });

    } else if (json.type === "delete_moment") {
        removeElement(json.value);
        // momentContainer.remove(document.getElementById())
    }
    // console.log(e.data.text);
};

function removeElement(elementId) {
    // Removes an element from the document
    var element = document.getElementById(elementId);
    element.parentNode.removeChild(element);
}

socket.onopen = function (e) {
    let response = {
        "type": "init",
        "value": username,
    };
    socket.send(JSON.stringify(response));
};
socket.onerror = function (e) {
    console.log(e);
};
socket.onclose = function (e) {

};