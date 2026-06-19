interface ModalProps {
  isOpen: boolean;
  title: string;
  onClose: () => void;
  children: React.ReactNode;
}

export function Modal({ isOpen, title, onClose, children }: ModalProps): JSX.Element | null {
  if (!isOpen) {
    return null;
  }

  return (
    <div className="fixed inset-x-0 top-0 z-50 flex items-start justify-center bg-orange-950/20 pt-16 sm:p-4 sm:pt-16">
      <div
        className="w-full max-w-3xl rounded-2xl border border-orange-100 bg-white shadow-xl flex flex-col overflow-x-hidden"
        style={{ maxHeight: "calc(100dvh - 4.5rem)" }}
      >
        <div className="flex-shrink-0 border-b border-orange-100 px-4 py-3 sm:px-6 sm:py-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-semibold text-orange-900 sm:text-lg">{title}</h2>
            <button
              type="button"
              onClick={onClose}
              className="rounded bg-orange-100 px-2 py-1 text-sm text-orange-900 hover:bg-orange-200"
            >
              X
            </button>
          </div>
        </div>
        <div className="flex-1 overflow-y-auto overflow-x-hidden px-4 py-3 sm:px-6 sm:py-4">
          {children}
        </div>
      </div>
    </div>
  );
}
