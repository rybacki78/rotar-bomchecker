function filterFunction() {
  const input = document.getElementById("root");
  const filter = input.value.toUpperCase();
  const dropdown = document.getElementById("dropdown-list");
  const items = dropdown.getElementsByClassName("dropdown-item");
  dropdown.style.display = "block";
  for (let i = 0; i < items.length; i++) {
    let txtValue = items[i].textContent || items[i].innerText;
    items[i].style.display =
      txtValue.toUpperCase().indexOf(filter) > -1 ? "" : "none";
  }
}
function showDropdown() {
  document.getElementById("dropdown-list").style.display = "block";
}
function hideDropdown() {
  setTimeout(() => {
    document.getElementById("dropdown-list").style.display = "none";
  }, 200);
}
function selectRoot(value) {
  document.getElementById("root").value = value;
  document.getElementById("dropdown-list").style.display = "none";
  document.getElementById("root").form.submit();
}

