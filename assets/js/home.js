var isAuthorized;
function updateSigninStatus(isSignedIn) {
  isAuthorized = isSignedIn;
  console.log(isAuthorized)
}

function onSignIn(googleUser) {
    // Useful data for your client-side scripts:
    var profile = googleUser.getBasicProfile();
    console.log("ID: " + profile.getId()); // Don't send this directly to your server!
    console.log('Full Name: ' + profile.getName());
    console.log('Given Name: ' + profile.getGivenName());
    console.log('Family Name: ' + profile.getFamilyName());
    console.log("Image URL: " + profile.getImageUrl());
    console.log("Email: " + profile.getEmail());

    let GoogleAuth = gapi.auth2.getAuthInstance();

    // The ID token you need to pass to your backend:
    var id_token = googleUser.getAuthResponse().id_token;
    GoogleAuth.isSignedIn.listen(updateSigninStatus);
    isAuthorized = true;
    console.log("ID Token: " + id_token);

    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/');
    xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
    xhr.onload = function() {
      // console.log('Signed in as: ' + xhr.responseText);
    };
    xhr.send('idtoken=' + id_token);
}

function signOut() {
    var auth2 = gapi.auth2.getAuthInstance();
    auth2.signOut().then(function () {
      // console.log('User signed out.');
    });
}