function badUsername(str) {
    return (str === ""||(str.length < 5) || (str.length > 15)||/\W/.test(str));
}

function onRegister(){
    let inviteCode = document.getElementById("id_invite_code").value;

    let username = document.getElementById("id_username").value;

    if (badUsername(username)){
        alert("BAD USERNAME");
        return false;
    }

    var postRequest = new XMLHttpRequest();
    console.log(window.location.href);
    postRequest.open('POST', window.location.href, true);
    postRequest.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
    postRequest.onload = function() {
      if (postRequest.responseText==="valid"){
          window.location.replace("/moments/"+username);
      }else if(postRequest.responseText==="invalid"){
          alert("Invalid Username!")
      }else if(postRequest.responseText==="bad_invite"){
          alert("Invalid Invitation Code!")
      }
    };

    const urlParams = new URLSearchParams(window.location.search);
    const id_token = urlParams.get('token');

    postRequest.send('username=' + username+'&googleToken='+id_token+'&inviteCode='+inviteCode);
    console.log("OK SENT! "+'username=' + username+'&googleToken='+id_token)

    return false;
}