const API="http://127.0.0.1:8000";

let accessToken=null;

let me=null;

let socket = null;

let currentConversation = null;

document
.getElementById("loginBtn")
.onclick=login;


async function login(){

    const email = document.getElementById("email").value;

    const password = document.getElementById("password").value;

    const response = await fetch(

        API + "/api/accounts/login/",

        {
            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({

                email: email,

                password: password

            })

        }

    );

    const data = await response.json();

    if(!response.ok){

        alert(data.error);

        return;

    }

    accessToken = data.access;

    localStorage.setItem("token", data.access);

    localStorage.setItem("refresh", data.refresh);

    localStorage.setItem("role", data.role);

    document.querySelector(".login-screen").classList.add("hidden");

    document.querySelector(".chat-screen").classList.remove("hidden");

    loadProfile();

}

async function loadProfile(){

    const response = await fetch(

        API + "/api/accounts/profile/",

        {

            headers:{

                Authorization:"Bearer " + accessToken

            }

        }

    );

    const data = await response.json();

    console.log(data);

    me = data;

    document.getElementById("myName").innerHTML =

        data.username;

    loadUsers();

}

async function loadUsers(){

    const response = await fetch(

        API + "/api/chat/users/",

        {

            headers:{
                Authorization:"Bearer " + accessToken
            }

        }

    );

    const users = await response.json();

    const usersDiv = document.getElementById("users");

    usersDiv.innerHTML = "";

    users.forEach(user=>{

        usersDiv.innerHTML += `

            <div
                class="user"
                onclick="startConversation(${user.id}, '${user.username}')">

                ${user.username}

            </div>

        `;

    });

}

async function startConversation(userId, username){

    document.getElementById("chatTitle").innerHTML = username;

    const response = await fetch(

        API + "/api/chat/conversations/create/",

        {

            method:"POST",

            headers:{
                "Content-Type":"application/json",
                Authorization:"Bearer " + accessToken
            },

            body:JSON.stringify({

                user:userId

            })

        }

    );

    const data = await response.json();

    console.log(data);

    currentConversation = data.id;

    loadMessages();

    connectSocket();

}
async function loadMessages(){

    const response = await fetch(

        API + "/api/chat/messages/" + currentConversation + "/",

        {

            headers:{

                Authorization:"Bearer " + accessToken

            }

        }

    );

    const messages = await response.json();

    const box = document.getElementById("messages");

    box.innerHTML = "";

    messages.forEach(message=>{

        addMessage(message);

    });

}
function addMessage(message){

    const box=document.getElementById("messages");

    const mine=message.sender.id===me.id;

    box.innerHTML+=`

        <div class="message ${mine?'me':'other'}">

            ${message.message}

        </div>

    `;

    box.scrollTop=box.scrollHeight;

}
function connectSocket(){

    if(socket){

        socket.close();

    }

    socket = new WebSocket(

        "ws://127.0.0.1:8000/ws/chat/" +

        currentConversation +

        "/"

    );

    socket.onmessage=function(event){

        const data = JSON.parse(event.data);

        addSocketMessage(data);

    };

}

function addSocketMessage(data){

    const box=document.getElementById("messages");

    const mine=data.sender_id===me.id;

    box.innerHTML+=`

        <div class="message ${mine?'me':'other'}">

            ${data.message}

        </div>

    `;

    box.scrollTop=box.scrollHeight;

}

document
.getElementById("sendBtn")
.onclick=function(){

    const input=document.getElementById("messageInput");

    if(input.value===""){

        return;

    }

    socket.send(

        JSON.stringify({

            message:input.value

        })

    );

    input.value="";

};