// import Dashboard from './dashboard';

// class App extends React.Component {

//     render() { 
//         return (
//             <section>
//                 <p>React Component Is Active 🤯</p>
//             </section>
//         );
//     }

// };

const { useEffect, useState } = React;

function App() {
    const [errors, setErrors] = useState(false);
    const [users, setUsers] = useState({});

    async function fetchData() {
        const res = await fetch(`https://0.0.0.0:5000/api/v1/users`);
        res
          .json()
          .then(res => setUsers(res.json()))
          .catch(() => setErrors(true));
    };

    useEffect(() => {
        fetchData();
    });
    
    console.log(users);
    console.log(errors)
    return (
        <section>
            {
                errors ?
                <p>Big Error</p> :
                <p>React Component Is Active 🤯 {users}</p> 
            }
        </section>
    );
}


ReactDOM.render(<App />, document.getElementById('root'));
  