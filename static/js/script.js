document.addEventListener(
    "DOMContentLoaded",
    function () {

        const form =
            document.getElementById(
                "comicForm"
            );

        const button =
            document.getElementById(
                "generateBtn"
            );

        if (!form || !button) {
            return;
        }


        form.addEventListener(
            "submit",
            function () {

                button.classList.add(
                    "loading"
                );

                button.innerHTML =
                    "✨ Creating your comic... Please wait";

                button.disabled = true;

            }
        );

    }
);