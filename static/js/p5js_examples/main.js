function setup() {
  canvasSize = createVector(windowWidth - 17, windowHeight - 17);
  createCanvas(canvasSize.x, canvasSize.y);
  availablePage = new AvailablePage(canvasSize.x, canvasSize.y);

    // background images
    backgroundGreenURL= "/static/images/green_background.png";
    imageBackgroundGreen = loadImage(backgroundGreenURL);
    
    backgroundRedURL= "/static/images/red_background.png";
    imageBackgroundRed = loadImage(backgroundRedURL);

  // testing values
  roomAvailable = true;
}

function draw() {
  if (roomAvailable) {
    background(imageBackgroundGreen);
    availablePage.Draw();
  } else {
    background(imageBackgroundRed);
    meetingPage.Draw();
  }
}
