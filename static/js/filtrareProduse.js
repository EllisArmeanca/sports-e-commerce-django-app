// document.getElementById("formular-filtru").addEventListener("submit", function(event) {
//   event.preventDefault(); // Previne reîncărcarea paginii

//   const form = document.getElementById('formular-filtru');
//   const dateFormular = new FormData(form);

//   // Obține CSRF token-ul din cookie
//   const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

//   fetch(filtreazaProduseUrl, {
//       method: "POST",
//       body: dateFormular,
//       headers: {
//           'X-CSRFToken': csrfToken,
//       }
//   })
//   .then(response => response.json())
//   .then(data => {
//       const listaProduse = document.getElementById('lista-produse');
//       listaProduse.innerHTML = ''; // Golește lista curentă

//       if (data.status === 'success') {
//           data.produse.forEach(produs => {
//               const listItem = document.createElement('li');
//               listItem.innerHTML = `
//                   <img src="${produs.imagine}" alt="${produs.nume}">
//                   <div>
//                     <h2>${produs.nume}</h2>
//                     <p>${produs.pret} lei</p>
//                   </div>
//               `;
//               listaProduse.appendChild(listItem);
//           });
//       } else {
//           listaProduse.innerHTML = `<li style="color: red;">Eroare: ${data.message}</li>`;
//       }
//   })
//   .catch(error => console.error("Eroare la obținerea produselor:", error));
// });
