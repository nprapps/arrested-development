/*
These strings, e.g. 'C0001', come from OneTrust, and can be edited in the "categorizations" section of OneTrust's app.
Be sure to update this file if you make changes in OneTrust's app.
This file also exists in the DM and ID/Auth codebases
 */
var STRICTLY_NECESSARY = 'C0001';
var PERFORMANCE_AND_ANALYTICS = 'C0002';
var FUNCTIONAL = 'C0003';
var TARGETING_AND_SPONSOR = 'C0004';
var SOCIAL_MEDIA = 'C0005';

function hasConsentedTo(category) {
  // checking for "window" because this could run in a windowless unit-test environment
  if (window && typeof window.OnetrustActiveGroups !== 'undefined') {
    return window.OnetrustActiveGroups.split(',').includes(category);
  }

  return true;
}

var googleAnalyticsAlreadyInitialized = false;

var setupGoogleAnalytics = function () {
  if (window.top !== window) {
    var gtagID = "G-LLLW9F9XPC";
  } else {
    var gtagID = "G-XK44GJHVBE";
  }
  // Bail early if opted out of Performance and Analytics consent groups
  if (!hasConsentedTo(PERFORMANCE_AND_ANALYTICS))
    return;

  var script = document.createElement("script");

  script.src = "https://www.googletagmanager.com/gtag/js?id=" + gtagID;

  script.async = true;

  var script_embed = document.createElement("script");

  script_embed.innerHTML =
    "window.dataLayer = window.dataLayer || [];function gtag(){dataLayer.push(arguments);}gtag('js', new Date());gtag('config', '" +
    gtagID +
    "', { 'send_page_view': false });";
  document.head.append(script, script_embed);

  if (window.top !== window) {
    // By default Google tracks the query string, but we want to ignore it.
    var here = new URL(window.location);

    // Custom dimensions & metrics
    var parentUrl = here.searchParams.has("parentUrl")
      ? new URL(here.searchParams.get("parentUrl"))
      : "";
    var parentHostname = "";

    if (parentUrl) {
      parentHostname = parentUrl.hostname;
    }

    var initialWidth = here.searchParams.get("initialWidth") || "";

    var customData = {};
    customData["dimension1"] = parentUrl;
    customData["dimension2"] = parentHostname;
    customData["dimension3"] = initialWidth;
  } else {
    // Secondary topics
    var dim6 = "";
    // Topic IDs
    var dim2 = "";

    // Google analytics doesn't accept arrays anymore, these must be strings.

    try {
      dim6 = window.PROJECT_ANALYTICS.secondaryTopics.join(", ");
    } catch (error) {
      console.log(
        "PROJECT_ANALYTICS.secondaryTopics is not an array, check project.json"
      );
    }

    try {
      dim2 = window.PROJECT_ANALYTICS.topicIDs.join(", ");
    } catch (error) {
      console.log(
        "PROJECT_ANALYTICS.topicIDs is not an array, check project.json"
      );
    }

    var customData = {};
    // customData["dimension2"] = dim2;
    customData["dimension3"] = window.PROJECT_ANALYTICS
      ? window.PROJECT_ANALYTICS.primaryTopic
      : "News";
    // customData["dimension6"] = dim6;
    customData["dimension22"] = document.title;
  }

  gtag("event", "page_view", customData);
  googleAnalyticsAlreadyInitialized = true;
};

// Add GA initialization to window.onload
function addLoadEvent(func) {
  var oldOnLoad = window.onload;
  if (typeof window.onload != "function") {
    window.onload = func;
  } else {
    window.onload = function () {
      if (oldOnLoad) {
        oldOnLoad();
      }
      func();
    };
  }
}

addLoadEvent(setupGoogleAnalytics);

// Listen for DataConsentChanged event
document.addEventListener("npr:DataConsentChanged", function() {
  // Bail early if it's already been set up
  if (googleAnalyticsAlreadyInitialized) return;

  // When a user opts into performance and analytics cookies, initialize GA
  if (hasConsentedTo(PERFORMANCE_AND_ANALYTICS)) {
    setupGoogleAnalytics();
  }
});