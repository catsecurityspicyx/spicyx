function fullscreenMeida(action, mediaAlvo, comment, commentAlvo) {
    /*
    * action = open || close
    * mediaAlvo = imageID
    * comment = true || false
    * commentAlvo = commentID
    * */
    var mediaAlvo = mediaAlvo || null
    var commentAlvo = commentAlvo || null

    if (comment == false) {
        if (action == "open") {
            document.getElementById(mediaAlvo).classList.remove("fullscreen-closed")
            document.getElementById(mediaAlvo).classList.add("bg-fullscreen");
        } else { //action = close
            document.getElementById(mediaAlvo).classList.remove("bg-fullscreen");
            document.getElementById(mediaAlvo).classList.add("fullscreen-closed");

            if (commentAlvo != null) {
                document.getElementById(commentAlvo).classList.add("invisible-content")
            }
        }
    } else { //comment = true
        if (action == "open") {
            document.getElementById(commentAlvo).classList.remove("invisible-content")
        } else { //action = close
            document.getElementById(commentAlvo).classList.add("invisible-content")
        }
    }
}

function fullscreenEditProfile(action, alvo, dataAlvo) {
    var dataAlvo = dataAlvo || null
    if (action == "open") {
        document.getElementById(alvo).classList.remove("fullscreen-closed")
        if (dataAlvo == 'bio') {
            document.getElementById('editbio').classList.remove("fullscreen-closed")
        } else if (dataAlvo == 'cover') {
            document.getElementById('editcover').classList.remove("fullscreen-closed")
        } else if (dataAlvo == 'name') {
            document.getElementById('editname').classList.remove("fullscreen-closed")
        } else if (dataAlvo == 'avatar') {
            document.getElementById('editavatar').classList.remove("fullscreen-closed")
        }

    } else { //action = close
        document.getElementById(alvo).classList.add("fullscreen-closed");
        document.getElementById('editbio').classList.add("fullscreen-closed");
        document.getElementById('editcover').classList.add("fullscreen-closed");
        document.getElementById('editname').classList.add("fullscreen-closed");
        document.getElementById('editavatar').classList.add("fullscreen-closed");
    }
}

function confirmation(status, postID) {
    var status = status || null
    if (status === 'open') {
        document.getElementById('confirm_action_container' + postID).style = 'display: flex'
        document.getElementById('confirm_action_container_for_close' + postID).style = 'display: flex'
    } else { //close
        document.getElementById('confirm_action_container' + postID).style = 'display: none'
        document.getElementById('confirm_action_container_for_close' + postID).style = 'display: none'
    }
}

function changeStatePostForm(action, alvo) {
    if (action == 'show') {
        document.getElementById(alvo).classList.toggle('invisible-content')
    }
}


function changeStateNotifications(action, alvo) {
    if (action == 'show') {
        document.getElementById(alvo).classList.toggle('visible-content')
        document.getElementById(alvo).classList.toggle('invisible-content')
    }
}


function selectViewContent(contentID) {
    if (contentID == 'free-feed') {
        document.getElementById(contentID).classList.remove("invisible-content");
        document.getElementById('premium-feed').classList.add("invisible-content");
    } else {
        document.getElementById(contentID).classList.remove("invisible-content");
        document.getElementById('free-feed').classList.add("invisible-content");
    }
}

function selectorMediaForPost(myOption) {
    document.getElementById('selector-media-post').style = 'display: none'
    if (myOption == 'mediaImage') {
        if (!document.getElementById('containerVideo').classList.contains('invisible-content')) {
            document.getElementById('containerVideo').classList.add('invisible-content')
        }
        document.getElementById('containerImage').classList.remove('invisible-content');
    } else {  //mediaVideo
        if (!document.getElementById('containerImage').classList.contains('invisible-content')) {
            document.getElementById('containerImage').classList.add('invisible-content')
        }
        document.getElementById('containerVideo').classList.remove('invisible-content')
    }
}

function returnToSelectorMedia(origin) {
    if (origin == 'containerVideo') {
        document.getElementById(origin).classList.add('invisible-content')
    } else {
        document.getElementById(origin).classList.add('invisible-content')
    }
    document.getElementById('selector-media-post').style = 'display: grid'
}

function postComment(postID) {
    document.getElementById(postID).classList.toggle('invisible-content');
}

function openDropdownMenu(postID) {
    document.getElementById(postID).classList.toggle('invisible-content');
}

window.onclick = function (event) {
    if (!event.target.matches('.post-menu-dropdown-icon') && !event.target.matches('.ellipsis')) {
        let dropdowns = document.getElementsByClassName("dropdown-container");
        let i;
        for (i = 0; i < dropdowns.length; i++) {
            let dropdownOpen = dropdowns[i];
            if (!dropdownOpen.classList.contains('invisible-content')) {
                dropdownOpen.classList.add('invisible-content');
            }
        }
    }
}