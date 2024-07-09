document.addEventListener('DOMContentLoaded', function () {
    $(".messages").animate({ scrollTop: $(document).height() }, "fast");

    $("#profile-img").click(function () {
        $("#status-options").toggleClass("active");
    });

    $(".expand-button").click(function () {
        $("#profile").toggleClass("expanded");
        $("#contacts").toggleClass("expanded");
    });

    $("#status-options ul li").click(function () {
        $("#profile-img").removeClass();
        $("#status-online").removeClass("active");
        $("#status-away").removeClass("active");
        $("#status-busy").removeClass("active");
        $("#status-offline").removeClass("active");
        $(this).addClass("active");

        if ($("#status-online").hasClass("active")) {
            $("#profile-img").addClass("online");
        } else if ($("#status-away").hasClass("active")) {
            $("#profile-img").addClass("away");
        } else if ($("#status-busy").hasClass("active")) {
            $("#profile-img").addClass("busy");
        } else if ($("#status-offline").hasClass("active")) {
            $("#profile-img").addClass("offline");
        } else {
            $("#profile-img").removeClass();
        };

        $("#status-options").removeClass("active");
    });

    function newUserMessage() {
        let message = $(".message-input input").val();
        if ($.trim(message) == '') {
            return false;
        }

        $('<li class="sent"><img src="https://avatars3.githubusercontent.com/u/30492527?s=460&v=4" alt="" /><p>' + message + '</p></li>').appendTo($('.messages ul'));
        $('.message-input input').val(null);
        $('.contact.active .preview').html('<span>You: </span>' + message);
        $(".messages").animate({ scrollTop: $(document).height() }, "fast");
        get_bot_response(message)

    };

    function newBotMessage(message) {
        $('<li class="replies"><img src="static/bot_pic.jpg" alt="" /><p>' + message["response"] + '</p></li>').appendTo($('.messages ul'));
        $(".messages").animate({ scrollTop: $(document).height() }, "slow");

    };

    $('.submit').click(function () {
        newUserMessage();
    });

    $(window).on('keydown', function (e) {
        if (e.which == 13) {
            newUserMessage();
            return false;
        }
    });


    function get_bot_response(message) {
        // Get the CSRF token from the cookie
        const csrftoken = getCookie('csrftoken');

        // Set up the AJAX request with the CSRF token
        $.ajax({
            url: '/user_message/',
            type: 'POST',
            data: {
                'message': message,
                'csrfmiddlewaretoken': csrftoken  // Include the CSRF token in the data
            },
            success: newBotMessage,
            complete: function () { },
            error: function (xhr, textStatus, thrownError) { }
        });
    }

    // Function to retrieve the CSRF token from the cookie
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                // Check if the cookie name matches the expected pattern
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    // Extract and decode the CSRF token
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }


    function show_bot_response(message) {
        console.log(message);
    }

    const uploadArea = document.getElementById('uploadArea');
    const uploadButton = document.getElementById('upload_kb_button');
    const closeButton = document.getElementById('close_upload_area');

    closeButton.addEventListener('click', function () {
        uploadArea.classList.toggle('show'); // Toggle the 'show' class
    });

    uploadButton.addEventListener('click', function () {
        uploadArea.classList.toggle('show'); // Toggle the 'show' class
    });
});
