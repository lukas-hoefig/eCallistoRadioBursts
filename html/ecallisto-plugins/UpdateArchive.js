// Function to format date as YYYY-MM-DD
function formatDate(date) {
    var year = date.getFullYear();
    var month = ('0' + (date.getMonth() + 1)).slice(-2);
    var day = ('0' + date.getDate()).slice(-2);
    return year + '/' + month + '/' + day + '/ROBUST_archive_' + year + month + day + '.zip';
}

function formatDateTxT(date) {
    var year = date.getFullYear();
    var month = ('0' + (date.getMonth() + 1)).slice(-2);
    var day = ('0' + date.getDate()).slice(-2);
    return year + '/' + month + '/' + day + '/ROBUST_Graz_' + year + '_' + month + '_' + day + '.txt';
}

// Function to update download link href with formatted date
function updateDownloadLink() {
    var dateInput = document.getElementById("datepicker_archive");
    var selectedDate = new Date(dateInput.value);
    var formattedDate = formatDate(selectedDate);
    var downloadLink = document.getElementById("download_archive_zip");
    downloadLink.href = "../../images/ROBUST/" + formattedDate; // Change '#' to actual download URL
    document.getElementById("download_archive_button_zip").style.display = "block";

    var formattedDatetxt = formatDateTxT(selectedDate);
    var downloadLinktxt = document.getElementById("download_archive_txt");
    downloadLinktxt.href = "../../images/ROBUST/" + formattedDatetxt; // Change '#' to actual download URL
    document.getElementById("download_archive_button_txt").style.display = "block";
}

// Add event listener to date input to update download link on input change
document.getElementById("datepicker_archive").addEventListener("input", updateDownloadLink);

// Initial call to update download link based on initial value of date input
//updateDownloadLink();
