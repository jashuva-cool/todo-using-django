function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(";").shift();
}

document.addEventListener("DOMContentLoaded", () => {
  const html = document.documentElement;
  const savedTheme = localStorage.getItem("taskflow-theme") || "light";
  html.setAttribute("data-bs-theme", savedTheme);

  document.querySelectorAll("#themeToggle").forEach((button) => {
    button.addEventListener("click", () => {
      const next = html.getAttribute("data-bs-theme") === "dark" ? "light" : "dark";
      html.setAttribute("data-bs-theme", next);
      localStorage.setItem("taskflow-theme", next);
    });
  });

  document.querySelectorAll(".toast").forEach((toastEl) => {
    new bootstrap.Toast(toastEl, { delay: 3500 }).show();
  });

  document.querySelectorAll(".task-toggle").forEach((toggle) => {
    toggle.addEventListener("change", async () => {
      const card = toggle.closest(".task-card");
      const response = await fetch(toggle.dataset.url, {
        method: "POST",
        headers: {
          "X-CSRFToken": getCookie("csrftoken"),
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: new URLSearchParams({ completed: toggle.checked ? "true" : "false" }),
      });
      if (response.ok) {
        const data = await response.json();
        card?.classList.toggle("task-complete", data.completed);
      } else {
        toggle.checked = !toggle.checked;
      }
    });
  });
});
