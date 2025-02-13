from firebase_setup import db

def get_challenges_list_service(uid, type):
    try:
        user_ref = db.collection('challenges').document(uid)
        user_doc = user_ref.get()

        # Si el documento no existe, lo creamos
        if not user_doc.exists:
            user_ref.set({})

        if type == 'physical':
            challenges = user_ref.collection('user_physical_challenges').stream()

        elif type == 'workouts':
            challenges = user_ref.collection('user_workouts_challenges').stream()
        
        else:
            print(f"Invalid type: {type}")
            return None

        challenges_list = []
        for challenge in challenges:
            challenges_data = challenge.to_dict()
            challenges_data['id'] = challenge.id
            challenges_list.append(challenges_data)

        return challenges_list
    
    except Exception as e:
        print(f"Error getting challenges: {e}")
        return None

def create_challenges_service(uid):
    try:
        user_ref = db.collection('challenges').document(uid)
        user_doc = user_ref.get()

        if not user_doc.exists:
            user_ref.set({})
        
        physical_challenges = user_ref.collection('user_physical_challenges')

        physical_challenges_list = ['Consistency is Key', 'Muscle Up!', 'Fat Loss Focus', 'Weight Watcher', 'Progress Pioneer']

        for challenge in physical_challenges_list:
            physical_challenges.document().set({
                'challenge': challenge,
                'state': False
            })
        
        workouts_challenges = user_ref.collection('user_workouts_challenges')

        workouts_challenges_list = ['Category Master', 'Endurance Streak', 'Strength Specialist', 'Sports Enthusiast', 'Calorie Crusher', 'Fitness Variety', 'Coach\'s Pick', 'Long Haul', 'Workout Titan']

        for challenge in workouts_challenges_list:
            workouts_challenges.document().set({
                'challenge': challenge,
                'state': False
            })
            
        return True
            
    except Exception as e:
        print(f"Error creating challenges: {e}")
        return False