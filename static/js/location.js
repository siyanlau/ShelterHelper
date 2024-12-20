document.addEventListener("DOMContentLoaded", function() {
    const numPieces = parseInt(document.querySelector('input[name="numPieces"]').value);

    for (let i = 1; i <= numPieces; i++) {
        const roomDropdown = document.getElementById(`roomNum${i}`);
        const shelfDropdown = document.getElementById(`shelfNum${i}`);

        roomDropdown.addEventListener("change", function() {
            const selectedRoom = this.value;

            // Clear existing shelf options
            shelfDropdown.innerHTML = "";

            if (locationData[selectedRoom]) {
                // Populate shelves for the selected room
                locationData[selectedRoom].forEach(function(shelf) {
                    const option = document.createElement("option");
                    option.value = shelf;
                    option.textContent = `Shelf ${shelf}`; // Corrected text content
                    shelfDropdown.appendChild(option);
                });
                shelfDropdown.disabled = false;
            } else {
                // Disable shelf dropdown if no shelves available
                shelfDropdown.disabled = true;
            }
        });
    }
});
