console.log('Disable right click script loaded');

document.addEventListener('contextmenu', function(e) {
    e.preventDefault();
});