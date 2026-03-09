export default function LoadingSpinner({ size = 'md' }: { size?: 'sm' | 'md' | 'lg' }) {
  const sizes = { sm: 'w-4 h-4', md: 'w-8 h-8', lg: 'w-12 h-12' }
  return (
    <div className="flex items-center justify-center p-8">
      <div className={`${sizes[size]} border-2 border-gray-700 border-t-aries-500 rounded-full animate-spin`} />
    </div>
  )
}
