var currentDate = new Date();

// Format the date as desired (e.g., "February 13, 2024")
var formattedDate = currentDate.toLocaleDateString('de-AT', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });

var yesterday = new Date(currentDate);
yesterday.setDate(currentDate.getDate() - 1);
var year = yesterday.getFullYear();
var month = ('0' + (yesterday.getMonth() + 1)).slice(-2); // Add leading zero if needed
var day = ('0' + yesterday.getDate()).slice(-2); // Add leading zero if needed
var formattedDateYesterday = year + '-' + month + '-' + day;

// Display the formatted date in the "currentDate" div
document.getElementById('currentDate').textContent = formattedDate;
document.getElementById('datepicker_archive').max = formattedDateYesterday;
document.getElementById('datepicker_archive').value = currentDate;

