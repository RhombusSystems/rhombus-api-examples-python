console.log("Rhombus URL is at " + url);

const video = document.querySelector("video");
const player = dashjs.MediaPlayer().create();
player.initialize(video, url, true);
