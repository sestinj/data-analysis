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
    const url = "https://niyqu0sase.execute-api.us-east-1.amazonaws.com/default/get-all-data"
    $.ajax({url:url, success: (response) => {
        console.log(response);
        response.forEach((data) => {
            $('#ticker-list').append(`<tr>
            <td>${data[8]}</td>
            <td>${data[2].toFixed(2)}</td>
            <td>${data[3].toFixed(2)}</td>
            <td>${data[4].toFixed(2)}</td>
            <td>${(100.0*(data[4]-data[2])/data[2]).toFixed(2)}%</td>
            </tr>`);
        });
        $('#ticker-list').after(`<p>*Data for ${data[0][1].split(" ")[0]}</p>`);
    }});
}

function loadMetabaseEmbed() {
    $.ajax(getFunctionURL('generateMetabaseEmbedURL')).done((response) => {
        $('#metabase-embed').attr('src', response);
    });
}

getAllTickers()
loadMetabaseEmbed()