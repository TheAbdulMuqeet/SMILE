document.addEventListener('DOMContentLoaded', function () {
    // Select Upload-Area
    const uploadArea = document.querySelector('#uploadArea');

    // Select Drop-Zoon Area
    const dropZoon = document.querySelector('#dropZoon');

    // Loading Text
    const loadingText = document.querySelector('#loadingText');

    // Select File Input 
    const fileInput = document.querySelector('#fileInput');

    // File-Details Area
    const fileDetails = document.querySelector('#fileDetails');

    // Uploaded File
    const uploadedFile = document.querySelector('#uploadedFile');

    // Uploaded File Info
    const uploadedFileInfo = document.querySelector('#uploadedFileInfo');

    // Uploaded File Name
    const uploadedFileName = document.querySelector('.uploaded-file__name');

    // Uploaded File Counter
    const uploadedFileCounter = document.querySelector('.uploaded-file__counter');

    // ToolTip Data
    const toolTipData = document.getElementsByClassName('upload-area__tooltip-data')[0];

    // Text File Types
    const textTypes = ["txt", "pl"];

    // Append Text File Types Array Inside Tooltip Data
    toolTipData.textContent = textTypes.join(', ');

    // When (dropZoon) has (dragover) Event 
    dropZoon.addEventListener('dragover', function (event) {
        event.preventDefault();
        dropZoon.classList.add('drop-zoon--over');
        console.log('Dragging over');
    });
    
    // When (dropZoon) has (dragleave) Event 
    dropZoon.addEventListener('dragleave', function (event) {
        dropZoon.classList.remove('drop-zoon--over');
        console.log('Dragging leave');
    });
    
    // When (dropZoon) has (drop) Event 
    dropZoon.addEventListener('drop', function (event) {
        event.preventDefault();
        dropZoon.classList.remove('drop-zoon--over');
        const file = event.dataTransfer.files[0];
        uploadFile(file);
    });
    
    // When (dropZoon) has (click) Event 
    dropZoon.addEventListener('click', function (event) {
        console.log('Click');
        fileInput.click();
    });

    // When (fileInput) has (change) Event 
    fileInput.addEventListener('change', function (event) {
        const file = event.target.files[0];
        uploadFile(file);
    });

    // Upload File Function
    function uploadFile(file) {
        const fileType = file.type;
        const fileSize = file.size;

        if (fileValidate(fileType, fileSize)) {
            dropZoon.classList.add('drop-zoon--Uploaded');
            loadingText.style.display = "block";
            uploadedFile.classList.remove('uploaded-file--open');
            uploadedFileInfo.classList.remove('uploaded-file__info--active');

            // Get CSRF token value from cookie
            const csrftoken = getCookie('csrftoken');

            const fileReader = new FileReader();
            fileReader.addEventListener('load', function () {
                const formData = new FormData();
                formData.append('file', file);
                const fileReader = new FileReader();
                fileReader.addEventListener('load', function () {
                    setTimeout(function () {
                        uploadArea.classList.add('upload-area--open');
                        loadingText.style.display = "none";
                        fileDetails.classList.add('file-details--open');
                        uploadedFile.classList.add('uploaded-file--open');
                        uploadedFileInfo.classList.add('uploaded-file__info--active');

                        // Display text content in the preview area
                        const textContent = fileReader.result;
                        textFilePreview.textContent = textContent; // Set text content in the preview area
                    }, 500); // 0.5s
                    uploadedFileName.textContent = file.name;
                    progressMove();
                });

                fileReader.readAsText(file);

                // Create XMLHttpRequest object
                const xhr = new XMLHttpRequest();

                // Set up the request
                xhr.open('POST', '/upload/', true);

                // Add CSRF token to request headers
                xhr.setRequestHeader('X-CSRFToken', csrftoken);

                // Set up onload event handler
                xhr.onload = function () {
                    if (xhr.status === 200) {
                        // Handle successful upload
                        console.log('File uploaded successfully');
                    } else {
                        // Handle upload errors
                        console.error('Error uploading file');
                    }
                };

                // Send the request
                xhr.send(formData);
            });

            fileReader.readAsDataURL(file);
        }
    }

    // Function to get CSRF token from cookie
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                // Check if cookie name matches the CSRF token cookie name
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Progress Counter Increase Function
    function progressMove() {
        let counter = 0;
        setTimeout(() => {
            let counterIncrease = setInterval(() => {
                if (counter === 100) {
                    clearInterval(counterIncrease);
                } else {
                    counter += 10;
                    uploadedFileCounter.textContent = `${counter}%`
                }
            }, 100);
        }, 600);
    }

    // Simple File Validate Function
    function fileValidate(fileType, fileSize) {
        let isText = textTypes.filter((type) => fileType.indexOf(`text/${type}`) !== -1);
        if (isText.length !== 0) {
            if (fileSize <= 2000000) { // 2MB :)
                return true;
            } else { // Else File Size
                alert('Please make sure your file is 2 Megabytes or less');
                return false;
            }
        } else { // Else File Type
            alert('Please make sure to upload a .txt file');
            return false;
        }
    }
});
