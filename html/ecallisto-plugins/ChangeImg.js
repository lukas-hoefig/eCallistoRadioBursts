// Function to change image source on hover
function changeImageSource(newSrc) {
    var img = document.getElementById('myImage');
    img.src = newSrc;
}

// Function to reset image source when not hovered
function resetImageSource() {
    var img = document.getElementById('myImage');
    img.src = 'default-image.png';
}