import { initializeApp } from 'firebase/app';
import { getAuth, onAuthStateChanged } from 'firebase/auth';
import { getFirestore } from 'firebase/firestore';

const firebaseApp = initializeApp({
  apiKey: "AIzaSyAp9sn0EJli86ELaO9idVcqLEGqckdFHYw",
  authDomain: "fredsocialbot.firebaseapp.com",
  projectId: "fredsocialbot",
  storageBucket: "fredsocialbot.appspot.com",
  messagingSenderId: "549259583933",
  appId: "1:549259583933:web:e6731addf1d073a2f932d4",
  measurementId: "G-F14PGKTZGZ"
});

const auth = getAuth(firebaseApp);
const db = getFirestore(firebaseApp);

// Detect auth state
onAuthStateChanged(auth, user => {
    if (user) {
        console.log('User is signed in')
    } else {
        console.log('User is not signed in')
    }
});
