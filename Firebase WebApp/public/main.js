function getAllTickers() {
    const url = " https://niyqu0sase.execute-api.us-east-1.amazonaws.com/default/get-all-tickers"
    $.ajax({url:url, success: (response) => {
        console.log(response)
        response.forEach((ticker) => {
            table.append(`<tr>
            <td>${ticker}}</td></tr>`);
        });
    }});
}
getAllTickers()