var isAuthorized;
function updateSigninStatus(isSignedIn) {
  isAuthorized = isSignedIn;
  console.log(isAuthorized)
}

function onSignIn(googleUser) {
    var profile = googleUser.getBasicProfile();

    let GoogleAuth = gapi.auth2.getAuthInstance();

    let id_token = googleUser.getAuthResponse().id_token;
    GoogleAuth.isSignedIn.listen(updateSigninStatus);
    isAuthorized = true;

    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/');
    xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
    //response format is login,username
    xhr.onload = function() {
      if (xhr.responseText.startsWith("login")){
          var username = xhr.responseText.split(",")[1];
          window.location.replace("/moments/"+username);
      }else if(xhr.responseText==="registration"){
          window.location.href = "/registration?token="+id_token;
      }
    };
    xhr.send('idtoken=' + id_token);

}

function signOut() {
    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/');
    xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
    xhr.send('logout=true');
    var auth2 = gapi.auth2.getAuthInstance();
    auth2.signOut().then(function () {
    });
}