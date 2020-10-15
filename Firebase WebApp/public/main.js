const functions = firebase.functions();

const DEVELOPMENT_MODE = true;
function getFunctionURL(name) {
    var prefix = 'https://us-central1-masstechfinancial.cloudfunctions.net/';
    if (DEVELOPMENT_MODE) {
        prefix = 'http://localhost:5001/masstechfinancial/us-central1/'
    }
    return prefix + name;
}

function getAllTickers() {
    const url = " https://niyqu0sase.execute-api.us-east-1.amazonaws.com/default/get-all-tickers"
    $.ajax({url:url, success: (response) => {
        console.log(response)
        response.forEach((ticker) => {
            $('#ticker-list').append(`<tr>
            <td>${ticker}</td></tr>`);
        });
    }});
}

function loadMetabaseEmbed() {
    $.ajax(getFunctionURL('generateMetabaseEmbedURL')).done((response) => {
        $('#metabase-embed').attr('src', response);
    });
}

getAllTickers()
loadMetabaseEmbed()