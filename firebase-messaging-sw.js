// firebase-messaging-sw.js
importScripts('https://www.gstatic.com/firebasejs/10.12.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/10.12.0/firebase-messaging-compat.js');

const firebaseConfig = {
    apiKey: "AIzaSyCfAJLC-pHvyVQylFIHoar5S9UrfzdxOoM",
    authDomain: "realchatkevtech.firebaseapp.com",
    projectId: "realchatkevtech",
    storageBucket: "realchatkevtech.firebasestorage.app",
    messagingSenderId: "1014431201308",
    appId: "1:1014431201308:web:8ce87def13bc97253607d9",
    measurementId: "G-PJ08TZ3TKT"
};

firebase.initializeApp(firebaseConfig);
const messaging = firebase.messaging();

// Background message handler context
messaging.onBackgroundMessage((payload) => {
    console.log('Background message received: ', payload);
    const notificationTitle = payload.notification.title;
    const notificationOptions = {
        body: payload.notification.body,
        icon: payload.notification.icon || '/static/images/logo.png'
    };
    self.registration.showNotification(notificationTitle, notificationOptions);
})