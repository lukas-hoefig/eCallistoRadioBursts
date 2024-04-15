fetch('/ecallisto-plugins/burstlist.json')
    .then(response => response.json())
    .then(data => loadbursts(data))
    .catch(error => console.error('Error fetching JSON:', error));

function loadbursts(data) {
    const bursts = data.bursts;
    const length = bursts.length

    document.getElementById('robust_latest_update').innerHTML = `Last Update:&nbsp${data.last_update}`;


    var linkElement = document.getElementById('robustdownload');
    var textfile = data.txt_filename;
    linkElement.href = textfile;

    document.getElementById('robust_newestfile').innerHTML = `Newest Data:&nbsp${data.newest_file}`;

    let output = ""
    if (!length) {
        output += "No Bursts yet";
        return;
    }
    else {
        output += "Burstliste:<br>"
        bursts.forEach((burst, indexb) => {
            const count = burst.stations.length;
            output += `${burst.time}&nbsp&nbsp&nbsp${burst.type}&nbsp&nbsp&nbsp`
            burst.stations.forEach((station, indexs) => {
                const link = station.file;
                output += `<a href="/images/ROBUST/current/${burst.name}/${link}" onmouseover="changeImageSource('/images/ROBUST/current/${burst.name}/${link}')">${station.name}</a>`;
                if (indexs !== count - 1) {
                    output += ", ";
                }

            });
            output += "<br>";
        });
    }
    document.getElementById('bursts').innerHTML = output;
}



