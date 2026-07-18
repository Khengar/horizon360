import { initializeApp, track, getCustomer, registerSchema } from './horizon360';

async function main() {
  // 1. Initialize the SDK (Do this once at server startup)
  try {
    await initializeApp({
      baseUrl: 'http://localhost:8000',
      username: 'root',
      password: 'root'
    });
    console.log('Horizon 360 SDK Initialized successfully.');
  } catch (error) {
    console.error('Failed to initialize CDP SDK:', error);
    process.exit(1);
  }

  // 2. Register Schema (Optional, typically handled in a setup script or admin panel)
  const cartSchema = {
    type: 'object',
    properties: {
      email: { type: 'string', format: 'email' },
      item_count: { type: 'number' }
    },
    required: ['email']
  };

  try {
    await registerSchema('cart.viewed', cartSchema);
    console.log('Schema registration complete.');
  } catch (error) {
    // Suppress error if schema already exists in the database
    console.log('Schema already registered or validation failed.');
  }

  // 3. Track Event (This can now be imported and used in any routing controller)
  console.log('Transmitting tracking event...');
  try {
    const trackResult = await track('cart.viewed', {
      email: 'backend_test@domain.com',
      item_count: 3
    });
    console.log('Tracking successful, Event ID:', trackResult.event_id);
  } catch (error) {
    console.error('Tracking payload rejected:', error);
  }

  // 4. Await Celery processing queue execution block
  await new Promise((resolve) => setTimeout(resolve, 2000));

  // 5. Retrieve Profile
  console.log('Fetching updated unified profile...');
  try {
    const profile = await getCustomer('backend_test@domain.com');
    console.log(JSON.stringify(profile, null, 2));
  } catch (error) {
    console.error('Profile extraction failed:', error);
  }
}

main();