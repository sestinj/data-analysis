const functions = require('firebase-functions');
require('dotenv').config();
// // Create and Deploy Your First Cloud Functions
// // https://firebase.google.com/docs/functions/write-firebase-functions
//
// exports.helloWorld = functions.https.onRequest((request, response) => {
//   functions.logger.info("Hello logs!", {structuredData: true});
//   response.send("Hello from Firebase!");
// });

// you will need to install via 'npm install jsonwebtoken' or in your package.json


//METABASE EMBED
exports.generateMetabaseEmbedURL = functions.https.onRequest((req, res) => {
    res.set('Access-Control-Allow-Origin', '*');
    
    var jwt = require("jsonwebtoken");
    var METABASE_SITE_URL = "http://chandler-metabase.herokuapp.com";
    var METABASE_SECRET_KEY = process.env.METABASE_SECRET_KEY;

    var payload = {
      resource: { dashboard: 1 },
      params: {},
      exp: Math.round(Date.now() / 1000) + (10 * 60) // 10 minute expiration
    };
    var token = jwt.sign(payload, METABASE_SECRET_KEY);

    var iframeUrl = METABASE_SITE_URL + "/embed/dashboard/" + token + "#bordered=true&titled=true";
    res.send(iframeUrl);
});
