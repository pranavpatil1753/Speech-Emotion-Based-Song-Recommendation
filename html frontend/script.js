document.addEventListener("DOMContentLoaded", () => {
    const loginForm = document.getElementById("loginForm");
    const signupForm = document.getElementById("signupForm");

    // ✅ ENHANCED DEBUG LOGIN HANDLER
    if (loginForm) {
        loginForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            console.log("🔹 Login form submitted!");

            const usernameInput = document.getElementById("username");
            const passwordInput = document.getElementById("password");

            if (!usernameInput || !passwordInput) {
                alert("❌ Form elements not found!");
                return;
            }

            const username = usernameInput.value.trim();
            const password = passwordInput.value.trim();

            if (!username || !password) {
                alert("❌ Please enter both username and password!");
                return;
            }

            console.log("🔹 Attempting login with:");
            console.log("   Username:", username);
            console.log("   Password length:", password.length);
            console.log("   Password (first 3 chars):", password.substring(0, 3) + "...");

            const loginData = { 
                username: username.toLowerCase(),
                password: password 
            };

            console.log("🔹 Sending login request:", loginData);

            try {
                const response = await fetch("http://127.0.0.1:5000/login", {
                    method: "POST",
                    headers: { 
                        "Content-Type": "application/json",
                        "Accept": "application/json"
                    },
                    body: JSON.stringify(loginData)
                });

                console.log("🔹 Response Status:", response.status);
                console.log("🔹 Response Headers:", [...response.headers.entries()]);

                // Get response text first to see exactly what server returns
                const responseText = await response.text();
                console.log("🔹 Raw Response Text:", responseText);

                // Try to parse as JSON
                let data;
                try {
                    data = JSON.parse(responseText);
                    console.log("🔹 Parsed Response Data:", data);
                } catch (parseError) {
                    console.error("❌ Failed to parse JSON:", parseError);
                    alert(`❌ Server returned invalid JSON: ${responseText}`);
                    return;
                }

                if (response.status === 401) {
                    console.error("❌ 401 Unauthorized - Invalid credentials");
                    console.log("🔍 This means the server rejected the username/password combination");
                    alert(`❌ Invalid credentials: ${data.error || data.message || "Username or password incorrect"}`);
                } else if (response.status === 200 && data.token) {
                    console.log("✅ Login successful!");
                    localStorage.setItem("token", data.token);
                    localStorage.setItem("username", username);
                    alert("✅ Login successful!");
                    window.location.href = "index.html";
                } else {
                    console.error("❌ Unexpected response:", response.status, data);
                    alert(`❌ Error: ${data.error || data.message || "Login failed"}`);
                }
            } catch (error) {
                console.error("❌ Network error:", error);
                alert(`❌ Network Error: ${error.message}`);
            }
        });
    }

    // ✅ ENHANCED DEBUG SIGNUP HANDLER
    if (signupForm) {
        signupForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            console.log("🔹 Signup form submitted!");

            const usernameInput = document.getElementById("new-username");
            const passwordInput = document.getElementById("new-password");
            const confirmPasswordInput = document.getElementById("confirm-password");

            if (!usernameInput || !passwordInput || !confirmPasswordInput) {
                alert("❌ Form elements not found!");
                return;
            }

            const username = usernameInput.value.trim();
            const password = passwordInput.value.trim();
            const confirmPassword = confirmPasswordInput.value.trim();

            if (!username || !password || !confirmPassword) {
                alert("❌ Please fill in all fields!");
                return;
            }

            if (password !== confirmPassword) {
                alert("❌ Passwords do not match!");
                return;
            }

            console.log("🔹 Attempting signup with:");
            console.log("   Username:", username);
            console.log("   Password length:", password.length);

            const signupData = { 
                username: username.toLowerCase(),
                password: password 
            };

            console.log("🔹 Sending signup request:", signupData);

            try {
                const response = await fetch("http://127.0.0.1:5000/signup", {
                    method: "POST",
                    headers: { 
                        "Content-Type": "application/json",
                        "Accept": "application/json"
                    },
                    body: JSON.stringify(signupData)
                });

                console.log("🔹 Signup Response Status:", response.status);

                const responseText = await response.text();
                console.log("🔹 Signup Raw Response:", responseText);

                let data;
                try {
                    data = JSON.parse(responseText);
                    console.log("🔹 Signup Parsed Data:", data);
                } catch (parseError) {
                    console.error("❌ Failed to parse signup JSON:", parseError);
                    alert(`❌ Server returned invalid JSON: ${responseText}`);
                    return;
                }

                if (response.status === 200 || response.status === 201) {
                    console.log("✅ Signup successful!");
                    alert("✅ Account created successfully! Please log in.");
                    window.location.href = "index.html";
                } else {
                    console.error("❌ Signup failed:", response.status, data);
                    alert(`❌ Signup Error: ${data.error || data.message || "Signup failed"}`);
                }
            } catch (error) {
                console.error("❌ Signup network error:", error);
                alert(`❌ Network Error: ${error.message}`);
            }
        });
    }

    // Add a test function to check server connection
    window.testServerConnection = async function() {
        console.log("🔄 Testing server connection...");
        try {
            const response = await fetch("http://127.0.0.1:5000/", {
                method: "GET"
            });
            console.log("🔹 Server test response:", response.status);
            const text = await response.text();
            console.log("🔹 Server test body:", text);
        } catch (error) {
            console.error("❌ Server connection test failed:", error);
        }
    };

    // Add a function to test with dummy credentials
    window.testDummyLogin = async function() {
        console.log("🔄 Testing with dummy credentials...");
        const testData = { username: "test", password: "test123" };
        
        try {
            const response = await fetch("http://127.0.0.1:5000/login", {
                method: "POST",
                headers: { 
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                body: JSON.stringify(testData)
            });
            
            console.log("🔹 Dummy login response:", response.status);
            const responseText = await response.text();
            console.log("🔹 Dummy login body:", responseText);
            
            try {
                const data = JSON.parse(responseText);
                console.log("🔹 Dummy login parsed:", data);
            } catch (e) {
                console.log("🔹 Response is not JSON");
            }
        } catch (error) {
            console.error("❌ Dummy login test failed:", error);
        }
    };

    console.log("🔧 Debug functions available:");
    console.log("   - testServerConnection()");
    console.log("   - testDummyLogin()");
});