export default function LoginPage() {
  return (
    <div className="flex h-screen items-center justify-center bg-gray-100">
      <div className="bg-white p-6 rounded-xl shadow w-96">
        <h2 className="text-xl font-bold mb-4">Login / Register</h2>

        <input placeholder="Email" className="input" />
        <input placeholder="Password" type="password" className="input mt-2" />

        <button className="btn mt-4 w-full">Continue</button>
      </div>
    </div>
  );
}
