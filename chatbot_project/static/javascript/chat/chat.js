var $messages = $('.messages-content');
var d, m;

// Initialize scrollbar on load
$(window).on('load', function () {
    $messages.mCustomScrollbar();
    setTimeout(function () {
        // Show welcome message on first load
        addMessage('bot', 'চাষের দিশায় স্বাগতম। আপনাকে কিভাবে সহায়তা করতে পারি? 🌾');
    }, 500);
});

// Keep scroll at bottom
function updateScrollbar() {
    $messages.mCustomScrollbar("update").mCustomScrollbar('scrollTo', 'bottom', {
        scrollInertia: 10,
        timeout: 0
    });
}

// Format timestamp (12-hour)
function getCurrentTime() {
    var now = new Date();
    var hours = now.getHours();
    var minutes = now.getMinutes();
    var ampm = hours >= 12 ? 'PM' : 'AM';
    hours = hours % 12 || 12;
    minutes = minutes < 10 ? '0' + minutes : minutes;
    return hours + ':' + minutes + ' ' + ampm;
}

// Add message to chat window
function addMessage(sender, text) {
    var messageClass = sender === 'user' ? 'message-personal' : 'new';
    var messageHtml = `<div class="message ${messageClass}">${text}<span class="timestamp">${getCurrentTime()}</span></div>`;
    $(messageHtml).appendTo($('.mCSB_container')).addClass('new');
    updateScrollbar();
}

// Send message event
function insertMessage() {
    var msg = $('.message-input').val().trim();
    if (msg === '') return false;

    // Show user message
    addMessage('user', msg);
    $('.message-input').val('');

    // Show bot typing indicator
    $('<div class="message loading new"><span></span></div>').appendTo($('.mCSB_container'));
    updateScrollbar();

    // Send message to Django backend
    $.get('/chat/', { message: msg })
        .done(function (data) {
            $('.message.loading').remove();
            // addMessage('bot', data.response);
            // If backend signals weather intent, ask for location
            if (data.response === '__ASK_WEATHER__') {
                requestWeather();
            } else {
                addMessage('bot', data.response);
            }
        })
        .fail(function () {
            $('.message.loading').remove();
            addMessage('bot', 'দুঃখিত, সার্ভারের সাথে সংযোগ করা যায়নি 😔');
        });
}

// Click send button
$('.message-submit').click(function () {
    insertMessage();
});

// Press Enter to send
$(window).on('keydown', function (e) {
    if (e.which === 13 && !e.shiftKey) {
        insertMessage();
        return false;
    }
});

// Optional: handle clear chat button (if template menu used)
function clearChat() {
    $('.mCSB_container').empty();
    addMessage('bot', 'চ্যাট সেশন পরিষ্কার করা হয়েছে 🧹');
}

// Add this function to request weather
function requestWeather() {
    addMessage('bot', 'আবহাওয়ার তথ্য আনা হচ্ছে...');

    if (!navigator.geolocation) {
        addMessage('bot', 'আপনার ব্রাউজার লোকেশন সাপোর্ট করে না।');
        return;
    }

    // Check permission state if supported
    if (navigator.permissions) {
        navigator.permissions.query({ name: 'geolocation' }).then(function (result) {
            if (result.state === 'granted' || result.state === 'prompt') {
                // Will prompt if not already granted
                getLocationAndSend();
            } else if (result.state === 'denied') {
                addMessage('bot', 'আপনি পূর্বে লোকেশন শেয়ার করতে অস্বীকার করেছেন। দয়া করে ব্রাউজার সেটিংস থেকে অনুমতি দিন।');
            }
        }).catch(function () {
            // Fallback if permissions API not supported
            getLocationAndSend();
        });
    } else {
        // Fallback for older browsers
        getLocationAndSend();
    }

    function getLocationAndSend() {
        navigator.geolocation.getCurrentPosition(
            function (position) {
                fetch('/get_weather/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        latitude: position.coords.latitude,
                        longitude: position.coords.longitude
                    })
                })
                .then(response => response.json())
                .then(data => {
                    addMessage('bot', data.weather);
                })
                .catch(() => {
                    addMessage('bot', 'আবহাওয়ার তথ্য আনতে সমস্যা হয়েছে।');
                });
            },
            function (error) {
                if (error.code === error.PERMISSION_DENIED) {
                    addMessage('bot', 'আপনি লোকেশন শেয়ার করেননি, তাই আবহাওয়ার তথ্য দেখানো যাচ্ছে না।');
                } else {
                    addMessage('bot', 'লোকেশন পাওয়া যায়নি, দয়া করে আবার চেষ্টা করুন।');
                }
            }
        );
    }
}