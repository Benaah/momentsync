function onLoad() {
    gapi.load('auth2', function () {
        gapi.auth2.init();
    });
}

$(function () {
    $('.lazy').lazy();
});

function signOut() {
    var xhr = new XMLHttpRequest();
    xhr.open('POST', window.location.href, true);
    xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
    xhr.send("logout=true");
    var auth2 = gapi.auth2.getAuthInstance();
    auth2.signOut().then(function () {
    });
    window.location.href = "https://momentsync.net";
}

function resizeListener() {
    var cameraDiv = document.getElementById("camera_id");
    if (isMobile()) {
        if (!document.getElementById("imgupload")) {
            var cameraInput = document.createElement("input");
            cameraInput.id = "imgupload";
            cameraInput.type = "file";
            cameraInput.name = "image";
            cameraInput.accept = "image/*";
            cameraInput.capture = "environment";
            cameraDiv.append(cameraInput);
            cameraInput.addEventListener('change', function () {
                var image = $('#imgupload').prop('files')[0];

                if (window.File && window.FileReader && window.FileList && window.Blob) {
                    var reader = new FileReader();
                    // Closure to capture the file information.
                    reader.addEventListener("load", function (e) {
                        const imageData = e.target.result;
                        window.loadImage(imageData, function (img) {
                            if (img.type === "error") {
                                console.log("couldn't load image:", img);
                            } else {
                                window.EXIF.getData(img, function () {
                                    var orientation = window.EXIF.getTag(this, "Orientation");
                                    var canvas = window.loadImage.scale(img, {
                                        orientation: orientation || 0,
                                        canvas: true
                                    });
                                    createTempLoadingImage();
                                    uploadBlobByStream(dataURLtoFile(canvas.toDataURL("image/jpeg", 0.75)));
                                    // or using jquery $("#container").append(canvas);
                                });
                            }
                        });
                    });
                    reader.readAsDataURL(image);
                } else {
                    console.log('The File APIs are not fully supported in this browser.');
                }
            })
        }
        // <input id="imgupload" type="file" name="image" accept="image/*" capture="environment">
    } else {
        removeElement("imgupload");
    }
}

resizeListener();

function isMobile() {
    var check = false;
    (function (a) {
        if (/(android|bb\d+|meego).+mobile|avantgo|bada\/|blackberry|blazer|compal|elaine|fennec|hiptop|iemobile|ip(hone|od)|iris|kindle|lge |maemo|midp|mmp|mobile.+firefox|netfront|opera m(ob|in)i|palm( os)?|phone|p(ixi|re)\/|plucker|pocket|psp|series(4|6)0|symbian|treo|up\.(browser|link)|vodafone|wap|windows ce|xda|xiino|android|ipad|playbook|silk/i.test(a) || /1207|6310|6590|3gso|4thp|50[1-6]i|770s|802s|a wa|abac|ac(er|oo|s\-)|ai(ko|rn)|al(av|ca|co)|amoi|an(ex|ny|yw)|aptu|ar(ch|go)|as(te|us)|attw|au(di|\-m|r |s )|avan|be(ck|ll|nq)|bi(lb|rd)|bl(ac|az)|br(e|v)w|bumb|bw\-(n|u)|c55\/|capi|ccwa|cdm\-|cell|chtm|cldc|cmd\-|co(mp|nd)|craw|da(it|ll|ng)|dbte|dc\-s|devi|dica|dmob|do(c|p)o|ds(12|\-d)|el(49|ai)|em(l2|ul)|er(ic|k0)|esl8|ez([4-7]0|os|wa|ze)|fetc|fly(\-|_)|g1 u|g560|gene|gf\-5|g\-mo|go(\.w|od)|gr(ad|un)|haie|hcit|hd\-(m|p|t)|hei\-|hi(pt|ta)|hp( i|ip)|hs\-c|ht(c(\-| |_|a|g|p|s|t)|tp)|hu(aw|tc)|i\-(20|go|ma)|i230|iac( |\-|\/)|ibro|idea|ig01|ikom|im1k|inno|ipaq|iris|ja(t|v)a|jbro|jemu|jigs|kddi|keji|kgt( |\/)|klon|kpt |kwc\-|kyo(c|k)|le(no|xi)|lg( g|\/(k|l|u)|50|54|\-[a-w])|libw|lynx|m1\-w|m3ga|m50\/|ma(te|ui|xo)|mc(01|21|ca)|m\-cr|me(rc|ri)|mi(o8|oa|ts)|mmef|mo(01|02|bi|de|do|t(\-| |o|v)|zz)|mt(50|p1|v )|mwbp|mywa|n10[0-2]|n20[2-3]|n30(0|2)|n50(0|2|5)|n7(0(0|1)|10)|ne((c|m)\-|on|tf|wf|wg|wt)|nok(6|i)|nzph|o2im|op(ti|wv)|oran|owg1|p800|pan(a|d|t)|pdxg|pg(13|\-([1-8]|c))|phil|pire|pl(ay|uc)|pn\-2|po(ck|rt|se)|prox|psio|pt\-g|qa\-a|qc(07|12|21|32|60|\-[2-7]|i\-)|qtek|r380|r600|raks|rim9|ro(ve|zo)|s55\/|sa(ge|ma|mm|ms|ny|va)|sc(01|h\-|oo|p\-)|sdk\/|se(c(\-|0|1)|47|mc|nd|ri)|sgh\-|shar|sie(\-|m)|sk\-0|sl(45|id)|sm(al|ar|b3|it|t5)|so(ft|ny)|sp(01|h\-|v\-|v )|sy(01|mb)|t2(18|50)|t6(00|10|18)|ta(gt|lk)|tcl\-|tdg\-|tel(i|m)|tim\-|t\-mo|to(pl|sh)|ts(70|m\-|m3|m5)|tx\-9|up(\.b|g1|si)|utst|v400|v750|veri|vi(rg|te)|vk(40|5[0-3]|\-v)|vm40|voda|vulc|vx(52|53|60|61|70|80|81|83|85|98)|w3c(\-| )|webc|whit|wi(g |nc|nw)|wmlb|wonu|x700|yas\-|your|zeto|zte\-/i.test(a.substr(0, 4))) check = true;
    })(navigator.userAgent || navigator.vendor || window.opera);
    return check;
}

//video BEGIN

// var video;
var videowidth, videoheight;
var canvas = document.createElement('canvas');
var context = canvas.getContext('2d');

// Put event listeners into place

if (!isMobile()) {
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

    }, false);
}


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

$(function () {
    "use strict";

    $('.topnav-right a').click(function (event) {
        event.preventDefault();
        signOut();
    });

    $(".camera_button").click(function () {
        if (!isMobile()) {
            $('header').removeClass('nav-down').addClass('nav-up');
            $(".camera_button").fadeOut();
            $(".camera-view").fadeIn();

            // let videoDisplay = $("video");

            canvas.width = videowidth;
            canvas.height = videoheight;

            // console.log(canvas.width);
            // console.log(canvas.height);

            // Trigger photo take
        }
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
        context.drawImage(video, 0, 0, canvas.width, canvas.height);
        var image = canvas.toDataURL("image/jpeg");  // here is the most important part because if you dont replace you will get a DOM 18 exception.
        createTempLoadingImage();
        uploadBlobByStream(dataURLtoFile(image));
    })

});

var tempQueue = [];
var tempID = 0;

function createTempLoadingImage() {
    var momentContainer = document.getElementById("moments");
    var moment = document.createElement("div");
    tempQueue.push(tempID);
    moment.id = "tempmoment_" + tempID++;
    moment.classList.add("column");
    moment.classList.add("is-one-quarter");
    moment.innerHTML = '<figure class="image is-5by4 popup"><img src="https://via.placeholder.com/250?text=Uploading..." alt="Moment"></figure>';
    momentContainer.prepend(moment);
}


let MD5 = new Hashes.MD5;

function getBlobService() {
    blobUri = 'https://' + 'cdn.momentsync.net';
    blobService = AzureStorage.Blob.createBlobServiceWithSas(blobUri, '?sv=2018-03-28&ss=b&srt=sco&sp=wac&se=2020-01-05T23:54:38Z&st=2019-01-05T15:54:38Z&spr=https,http&sig=g4yUqdENm2Ki1Y41yb0elw8%2BNPPvxVmYYcVCOaQg3rI%3D');

    return blobService;
}

function uploadBlobByStream(image) {
    var name = Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
    var file = image;

    var blobService = getBlobService();
    if (!blobService)
        return;

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
            contentType: "image/jpeg"
        }
    };
    blobService.singleBlobPutThresholdInBytes = blockSize;

    hashedName = MD5.hex(name);

    var speedSummary = blobService.createBlockBlobFromBrowserFile("momentsync", hashedName, file, options, function (error, result, response) {
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

        var moment = document.getElementById("tempmoment_" + tempQueue.shift());
        if (moment) {
            moment.id = json.value;
            moment.innerHTML = '<figure class="image is-5by4 popup"><img class="lazy" src="https://via.placeholder.com/250?text=Loading..." alt="Moment" data-src="https://cdn.momentsync.net/momentsync/' + json.value + '"></figure>';
        } else {
            moment = document.createElement("div");
            moment.id = json.value;
            moment.classList.add("column");
            moment.classList.add("is-one-quarter");
            moment.innerHTML = '<figure class="image is-5by4 popup"><img class="lazy" src="https://via.placeholder.com/250?text=Loading..." alt="Moment" data-src="https://cdn.momentsync.net/momentsync/' + json.value + '"</figure>';
            momentContainer.prepend(moment);
        }

        $('.lazy').lazy();

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
    if (element)
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