document.addEventListener("DOMContentLoaded", function() {
    const mainCategoryDropdown = document.getElementById("mainCategory");
    const subCategoryDropdown = document.getElementById("subCategory");

    // Listen for changes in the main category dropdown
    mainCategoryDropdown.addEventListener("change", function() {
        const selectedCategory = this.value;

        // Clear existing subcategory options
        subCategoryDropdown.innerHTML = "";

        // Populate subcategories if the main category exists in categoryData
        if (categoryData[selectedCategory]) {
            subCategoryDropdown.disabled = false;
            categoryData[selectedCategory].forEach(function(subCategory) {
                const option = document.createElement("option");
                option.value = subCategory;
                option.textContent = subCategory;
                subCategoryDropdown.appendChild(option);
            });
        } else {
            // Disable subcategory dropdown if no valid options
            subCategoryDropdown.disabled = true;
        }
    });
});
