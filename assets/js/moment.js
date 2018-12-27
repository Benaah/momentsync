function getBlobService() {
    blobUri = 'https://' + 'myhz.blob.core.windows.net';
    // blobUri = 'https://' + 'storage.markyhzhang.com';
    blobService = AzureStorage.Blob.createBlobServiceWithSas(blobUri, '?sv=2018-03-28&ss=b&srt=o&sp=c&se=2019-12-27T12:01:42Z&st=2018-12-27T04:01:42Z&spr=https&sig=D%2FN9Loq%2Fp60xBVbcK6BaUjttORWQNjM4g1a0chSXpA8%3D');

    return blobService;
}


function uploadBlobByStream(checkMD5) {
    var files = document.getElementById('files').files;
    if (!files.length) {
        alert('Please select a file!');
        return;
    }
    var file = files[0];

    var blobService = getBlobService();
    if (!blobService)
        return;

    var btn = document.getElementById('upload-button');
    btn.disabled = true;
    btn.innerHTML = 'Uploading';

    // Make a smaller block size when uploading small blobs
    var blockSize = file.size > 1024 * 1024 * 32 ? 1024 * 1024 * 4 : 1024 * 512;
    var options = {
        storeBlobContentMD5 : checkMD5,
        blockSize : blockSize
    };
    blobService.singleBlobPutThresholdInBytes = blockSize;

    var finishedOrError = false;
    var speedSummary = blobService.createBlockBlobFromBrowserFile("momentsync", file.name, file, options, function(error, result, response) {
        finishedOrError = true;
        btn.disabled = false;
        btn.innerHTML = 'UploadBlob';
        if (error) {
            alert('Upload failed, open browser console for more detailed info.');
            console.log(error);
        } else {
            setTimeout(function() { // Prevent alert from stopping UI progress update
                alert('Upload successfully!');
            }, 1000);
        }
    });
}