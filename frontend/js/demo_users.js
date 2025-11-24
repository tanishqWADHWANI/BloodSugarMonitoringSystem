// Seed demo users/patients/specialists in localStorage for local preview
(function(){
  try {
    const demoUsers = [
      { user_id: 1, first_name: 'Alice', last_name: 'Lee', email: 'alice@example.com', phone: '+1 555 100 001', date_of_birth: '1985-04-12', role: 'patient', status: 'Active' },
      { user_id: 2, first_name: 'Bob', last_name: 'Ray', email: 'bob@example.com', phone: '+1 555 100 002', date_of_birth: '1978-09-03', role: 'patient', status: 'Active' },
      { user_id: 3, first_name: 'Dr. Christina', last_name: 'Lee', email: 'clee@clinic', phone: '+1 555 200 003', date_of_birth: '1975-01-15', role: 'specialist', status: 'Active' },
      { user_id: 4, first_name: 'Staff', last_name: 'Member', email: 'staff@clinic', phone: '+1 555 300 004', date_of_birth: '1990-06-20', role: 'staff', status: 'Active' },
      { user_id: 5, first_name: 'Admin', last_name: 'User', email: 'admin@clinic', phone: '+1 555 400 005', date_of_birth: '1980-02-28', role: 'admin', status: 'Active' }
    ];

    // seed users list if not present
    const usersKey = 'demo_users_v1'; // internal marker
    if (!localStorage.getItem(usersKey)) {
      try { localStorage.setItem('users', JSON.stringify(demoUsers)); } catch(e){}
      localStorage.setItem(usersKey, '1');
    } else {
      // ensure users key exists
      if (!localStorage.getItem('users')) {
        try { localStorage.setItem('users', JSON.stringify(demoUsers)); } catch(e){}
      }
    }

    // seed specialists list (for selects)
    if (!localStorage.getItem('specialists')) {
      const specs = [
        { username: 'jsmith', full_name: 'Dr. John Smith', email: 'jsmith@demo', id: 101 },
        { username: 'ajones', full_name: 'Dr. Alex Jones', email: 'ajones@demo', id: 102 },
        { username: 'clee', full_name: 'Dr. Christina Lee', email: 'clee@clinic', id: 3 }
      ];
      try { localStorage.setItem('specialists', JSON.stringify(specs)); } catch(e){}
    }

    // seed patients array in standardized shape
    if (!localStorage.getItem('patients')) {
      const patients = [
        { number: '001', name: 'John Doe', age: 45, gender: 'Male', phone: '555-1234', medical_history: 'Type 2 Diabetes, Hypertension', lastChecked: 'Blood Sugar: 130 mg/dL, BP: 140/90 mmHg', id: '001', patientId: '001' },
        { number: '002', name: 'Alice Lee', age: 40, gender: 'Female', phone: '+1 555 100 001', medical_history: '', lastChecked: '', id: '002', patientId: '002' },
        { number: '003', name: 'Bob Ray', age: 47, gender: 'Male', phone: '+1 555 100 002', medical_history: '', lastChecked: '', id: '003', patientId: '003' }
      ];
      try { localStorage.setItem('patients', JSON.stringify(patients)); } catch(e){}
    } else {
      // ensure John Doe present
      try {
        const raw = localStorage.getItem('patients');
        let arr = raw ? JSON.parse(raw) : null;
        if (!Array.isArray(arr)) {
          // convert map to array
          arr = Object.values(arr || {});
        }
        const found = arr && arr.some(p => String(p.number) === '001' || String(p.id) === '001' || (p.name && p.name.includes('John Doe')));
        if (!found) {
          arr.unshift({ number: '001', name: 'John Doe', age: 45, gender: 'Male', phone: '555-1234', medical_history: 'Type 2 Diabetes, Hypertension', lastChecked: 'Blood Sugar: 130 mg/dL, BP: 140/90 mmHg', id: '001', patientId: '001' });
          try { localStorage.setItem('patients', JSON.stringify(arr)); } catch(e){}
        }
      } catch(e){}
    }

  } catch (err) { console.warn('demo_users seed failed', err); }
})();
